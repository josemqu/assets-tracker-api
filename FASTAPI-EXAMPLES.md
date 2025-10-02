# 🐍 FastAPI Backend Examples - Investment Tracker

Ejemplos de implementación con FastAPI, MongoDB y Motor.

---

## 📁 Estructura del Proyecto

```text
investment-tracker-api/
├── requirements.txt
├── .env
├── main.py
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   │   ├── user.py
│   │   ├── investment.py
│   │   └── config_site.py
│   ├── routers/
│   │   ├── auth.py
│   │   └── investments.py
│   ├── middleware/
│   │   └── auth.py
│   └── utils/
│       └── security.py
```

---

## 📦 requirements.txt

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
motor==3.3.2
pydantic==2.5.3
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
slowapi==0.1.9
pymongo==4.6.1
python-dotenv==1.0.0
```

---

## 🚀 main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import auth, investments


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(
    title="Investment Tracker API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(investments.router, prefix="/api/investments", tags=["investments"])


@app.get("/health")
async def health():
    return {"status": "OK"}
```

---

## ⚙️ app/config.py

```python
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7
    
    MONGODB_URI: str
    ALLOWED_ORIGINS: List[str] = ["http://localhost:8000"]
    RATE_LIMIT_PER_MINUTE: int = 100
    
    class Config:
        env_file = ".env"


settings = Settings()
```

---

## 🗄️ app/database.py

```python
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client: AsyncIOMotorClient = None
db = None


async def connect_to_mongo():
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client.get_database()
    
    # Crear índices
    await db.users.create_index("email", unique=True)
    await db.investments.create_index(
        [("user_id", 1), ("timestamp", 1), ("entidad", 1)],
        unique=True
    )
    
    print("✅ MongoDB connected")


async def close_mongo_connection():
    global client
    if client:
        client.close()


def get_database():
    return db
```

---

## 🔐 app/utils/security.py

```python
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None
```

---

## 🔒 app/middleware/auth.py

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.security import decode_access_token
from app.database import get_database
from bson import ObjectId

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    db = get_database()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )
    
    return user
```

---

## 📊 app/models/user.py

```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    userId: str
    email: str
    name: Optional[str] = None
    token: str
```

---

## 📈 app/models/investment.py

```python
from pydantic import BaseModel
from typing import Optional


class InvestmentCreate(BaseModel):
    timestamp: int
    entidad: str
    monto_ars: Optional[float] = None
    monto_usd: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": 1704067200000,
                "entidad": "Banco Nación",
                "monto_ars": 150000.50,
                "monto_usd": None
            }
        }


class InvestmentUpdate(BaseModel):
    monto_ars: Optional[float] = None
    monto_usd: Optional[float] = None
```

---

## 🔑 app/routers/auth.py

```python
from fastapi import APIRouter, HTTPException, status
from app.models.user import UserCreate, UserLogin, UserResponse
from app.database import get_database
from app.utils.security import (
    get_password_hash,
    verify_password,
    create_access_token
)
from datetime import datetime

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    db = get_database()
    
    # Verificar si el usuario existe
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Crear usuario
    user_dict = {
        "email": user.email,
        "password_hash": get_password_hash(user.password),
        "name": user.name,
        "preferences": {},
        "created_at": datetime.utcnow(),
        "last_login": None
    }
    
    result = await db.users.insert_one(user_dict)
    user_id = str(result.inserted_id)
    
    # Generar token
    token = create_access_token({"user_id": user_id, "email": user.email})
    
    return UserResponse(
        userId=user_id,
        email=user.email,
        name=user.name,
        token=token
    )


@router.post("/login", response_model=UserResponse)
async def login(credentials: UserLogin):
    db = get_database()
    
    # Buscar usuario
    user = await db.users.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )
    
    # Verificar contraseña
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )
    
    # Actualizar último login
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Generar token
    user_id = str(user["_id"])
    token = create_access_token({"user_id": user_id, "email": user["email"]})
    
    return UserResponse(
        userId=user_id,
        email=user["email"],
        name=user.get("name"),
        token=token
    )


@router.get("/validate")
async def validate_token(current_user: dict = Depends(get_current_user)):
    return {
        "success": True,
        "data": {
            "valid": True,
            "userId": str(current_user["_id"]),
            "email": current_user["email"]
        }
    }
```

---

## 📊 app/routers/investments.py

```python
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from app.models.investment import InvestmentCreate, InvestmentUpdate
from app.middleware.auth import get_current_user
from app.database import get_database
from bson import ObjectId
from datetime import datetime

router = APIRouter()


@router.get("/")
async def get_investments(
    entity: Optional[str] = None,
    date_from: Optional[int] = None,
    date_to: Optional[int] = None,
    limit: int = Query(1000, le=1000),
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    user_id = current_user["_id"]
    
    # Construir filtro
    filter_query = {"user_id": user_id}
    
    if entity:
        filter_query["entidad"] = entity
    
    if date_from or date_to:
        filter_query["timestamp"] = {}
        if date_from:
            filter_query["timestamp"]["$gte"] = date_from
        if date_to:
            filter_query["timestamp"]["$lte"] = date_to
    
    # Consultar
    cursor = db.investments.find(filter_query).sort("timestamp", -1).skip(offset).limit(limit)
    investments = await cursor.to_list(length=limit)
    
    total = await db.investments.count_documents(filter_query)
    
    # Convertir ObjectId a string
    for inv in investments:
        inv["_id"] = str(inv["_id"])
        inv["user_id"] = str(inv["user_id"])
    
    return {
        "success": True,
        "data": investments,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "hasMore": total > offset + len(investments)
        }
    }


@router.post("/")
async def create_investment(
    investment: InvestmentCreate,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    user_id = current_user["_id"]
    
    # Verificar si existe
    existing = await db.investments.find_one({
        "user_id": user_id,
        "timestamp": investment.timestamp,
        "entidad": investment.entidad
    })
    
    if existing:
        # Actualizar
        await db.investments.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "monto_ars": investment.monto_ars,
                    "monto_usd": investment.monto_usd,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return {"success": True, "isUpdate": True}
    
    # Crear nuevo
    investment_dict = investment.model_dump()
    investment_dict["user_id"] = user_id
    investment_dict["created_at"] = datetime.utcnow()
    investment_dict["updated_at"] = datetime.utcnow()
    
    result = await db.investments.insert_one(investment_dict)
    
    return {
        "success": True,
        "data": {"id": str(result.inserted_id)},
        "isUpdate": False
    }


@router.delete("/{investment_id}")
async def delete_investment(
    investment_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    user_id = current_user["_id"]
    
    result = await db.investments.delete_one({
        "_id": ObjectId(investment_id),
        "user_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro no encontrado"
        )
    
    return {"success": True, "message": "Registro eliminado"}
```

---

## 🚀 Ejecución

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# Iniciar servidor
uvicorn main:app --reload --port 8000

# Ver documentación interactiva
open http://localhost:8000/docs
```

---

## 📝 Deployment en Render

```yaml
# render.yaml
services:
  - type: web
    name: investment-tracker-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: MONGODB_URI
        sync: false
      - key: JWT_SECRET
        generateValue: true
      - key: ENVIRONMENT
        value: production
```

---

**Ver API-BACKEND-SPEC.md para especificación completa de endpoints.**
