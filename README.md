# 📡 Investment Tracker API

Backend API para la extensión Chrome Investment Tracker. Permite sincronización multi-dispositivo, backup en la nube y almacenamiento ilimitado de datos de inversión.

## 🚀 Stack Tecnológico

- **Framework**: FastAPI 0.109.0
- **Database**: MongoDB Atlas (Motor async driver)
- **Authentication**: JWT (JSON Web Tokens)
- **Validation**: Pydantic v2
- **Server**: Uvicorn

## 📋 Características

- ✅ Autenticación segura con JWT
- ✅ CRUD completo de inversiones
- ✅ Configuración de sitios web
- ✅ Sincronización bidireccional (push/pull)
- ✅ Export/Import de datos
- ✅ CORS configurado para Chrome Extension
- ✅ Documentación interactiva (Swagger/ReDoc)

## 🏗️ Estructura del Proyecto

```
investment-tracker-api/
├── main.py                 # Punto de entrada de la aplicación
├── requirements.txt        # Dependencias Python
├── .env                    # Variables de entorno (crear desde .env.example)
├── app/
│   ├── config.py          # Configuración de la aplicación
│   ├── database.py        # Conexión a MongoDB
│   ├── models/            # Modelos Pydantic
│   │   ├── user.py
│   │   ├── investment.py
│   │   └── config_site.py
│   ├── routers/           # Endpoints de la API
│   │   ├── auth.py        # Autenticación (register, login, validate)
│   │   ├── investments.py # CRUD de inversiones
│   │   ├── config.py      # Configuración y preferencias
│   │   └── sync.py        # Sincronización y export/import
│   ├── middleware/
│   │   └── auth.py        # Middleware de autenticación JWT
│   └── utils/
│       └── security.py    # Utilidades de seguridad (hash, JWT)
```

## ⚙️ Instalación

### 1. Clonar el repositorio

```bash
cd assets-tracker-api
```

### 2. Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env` con tus valores:

```env
ENVIRONMENT=development
PORT=8000

# Generar un secreto seguro: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET=tu-secreto-jwt-super-seguro

# MongoDB Atlas connection string
MONGODB_URI=mongodb+srv://usuario:contraseña@cluster.mongodb.net/investment-tracker?retryWrites=true&w=majority

# CORS - añadir el ID de tu extensión Chrome
ALLOWED_ORIGINS=http://localhost:8000,chrome-extension://tu-extension-id
```

### 5. Ejecutar el servidor

```bash
# Modo desarrollo (con auto-reload)
uvicorn main:app --reload --port 8000

# Modo producción
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📚 Documentación de la API

Una vez iniciado el servidor, puedes acceder a:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔌 Endpoints Principales

### Autenticación

- `POST /api/auth/register` - Registrar nuevo usuario
- `POST /api/auth/login` - Iniciar sesión
- `GET /api/auth/validate` - Validar token JWT

### Inversiones

- `GET /api/investments` - Obtener todas las inversiones
- `POST /api/investments` - Crear o actualizar inversión
- `POST /api/investments/bulk` - Crear múltiples inversiones
- `PUT /api/investments/{id}` - Actualizar inversión específica
- `DELETE /api/investments/{id}` - Eliminar inversión
- `DELETE /api/investments` - Eliminar todas las inversiones

### Configuración

- `GET /api/config/sites` - Obtener configuraciones de sitios
- `POST /api/config/sites` - Crear configuración de sitio
- `PUT /api/config/sites/{id}` - Actualizar configuración
- `DELETE /api/config/sites/{id}` - Eliminar configuración

### Preferencias de Usuario

- `GET /api/user/preferences` - Obtener preferencias
- `PUT /api/user/preferences` - Actualizar preferencias

### Sincronización

- `GET /api/sync/status` - Estado de sincronización
- `POST /api/sync/push` - Enviar datos al servidor
- `GET /api/sync/pull` - Obtener datos desde el servidor

### Export/Import

- `GET /api/export` - Exportar todos los datos
- `POST /api/import` - Importar datos (merge o replace)

## 🔐 Autenticación

Todos los endpoints (excepto `/api/auth/register` y `/api/auth/login`) requieren autenticación JWT.

### Ejemplo de uso:

```javascript
// 1. Registrar usuario
const response = await fetch('http://localhost:8000/api/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'securepassword123',
    name: 'Usuario Test'
  })
});

const { data } = await response.json();
const token = data.token;

// 2. Usar token en requests
const investments = await fetch('http://localhost:8000/api/investments', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
```

## 🗄️ Base de Datos

### MongoDB Atlas Setup

1. Crear cuenta en [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Crear un nuevo cluster (free tier disponible)
3. Crear un usuario de base de datos
4. Agregar tu IP a la whitelist (o usar 0.0.0.0/0 para desarrollo)
5. Obtener el connection string y agregarlo a `.env`

### Collections

- **users**: Usuarios registrados
- **investments**: Registros de inversiones
- **config_sites**: Configuraciones de sitios web

Los índices se crean automáticamente al iniciar la aplicación.

## 🚢 Despliegue

### Opción 1: Railway

1. Crear cuenta en [railway.app](https://railway.app)
2. Nuevo proyecto → Deploy from GitHub
3. Agregar variables de entorno
4. Deploy automático

### Opción 2: Render

1. Crear cuenta en [render.com](https://render.com)
2. New Web Service → Connect GitHub repo
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Agregar variables de entorno

### Opción 3: Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t investment-tracker-api .
docker run -p 8000:8000 --env-file .env investment-tracker-api
```

## 🧪 Testing

### Probar endpoints con curl

```bash
# Registrar usuario
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test12345","name":"Test User"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test12345"}'

# Crear inversión (usar token del login)
curl -X POST http://localhost:8000/api/investments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"timestamp":1704067200000,"entidad":"Banco Nación","monto_ars":150000.50}'
```

## 📖 Documentación Adicional

- [API-BACKEND-SPEC.md](./API-BACKEND-SPEC.md) - Especificación completa de la API
- [FASTAPI-EXAMPLES.md](./FASTAPI-EXAMPLES.md) - Ejemplos de implementación

## 🔧 Desarrollo

### Generar JWT Secret

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Logs

Los logs se muestran en la consola. En producción, considera usar un servicio de logging como Sentry o LogDNA.

## 🤝 Soporte

Para reportar problemas o solicitar nuevas funcionalidades, abre un issue en el repositorio.

## 📄 Licencia

MIT License

---

**Autor**: Investment Tracker Team  
**Versión**: 1.0.0  
**Última actualización**: Enero 2025
