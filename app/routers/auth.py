from fastapi import APIRouter, HTTPException, status, Depends
from app.models.user import UserCreate, UserLogin, UserResponse
from app.database import get_database
from app.utils.security import (
    get_password_hash,
    verify_password,
    create_access_token
)
from app.middleware.auth import get_current_user
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
