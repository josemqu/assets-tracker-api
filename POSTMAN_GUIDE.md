# 📮 Guía de Uso - Postman Collection

Colección completa de Postman para probar todos los endpoints de la Investment Tracker API.

## 📥 Importar en Postman

### 1. Importar la Colección

1. Abre Postman
2. Click en **Import** (esquina superior izquierda)
3. Arrastra o selecciona el archivo: `Investment_Tracker_API.postman_collection.json`
4. Click en **Import**

### 2. Importar los Environments

Importa ambos environments para poder cambiar fácilmente entre producción y local:

**Production Environment:**
- Archivo: `Investment_Tracker_Production.postman_environment.json`
- Base URL: `https://assets-tracker-api.up.railway.app`

**Local Environment:**
- Archivo: `Investment_Tracker_Local.postman_environment.json`
- Base URL: `http://localhost:8000`

Para importarlos:
1. Click en **Import** nuevamente
2. Selecciona los archivos `.postman_environment.json`
3. Click en **Import**

### 3. Seleccionar Environment

En la esquina superior derecha de Postman:
1. Click en el dropdown que dice "No Environment"
2. Selecciona **"Investment Tracker - Production"** o **"Investment Tracker - Local"**

## 🚀 Flujo de Pruebas

### Paso 1: Autenticación

Primero debes registrarte o hacer login:

1. **Registrar nuevo usuario:**
   - Endpoint: `Authentication > Register User`
   - Modifica el email en el body si es necesario
   - Click en **Send**
   - ✅ El token se guardará automáticamente

2. **O hacer Login con usuario existente:**
   - Endpoint: `Authentication > Login`
   - Usa el mismo email/password
   - Click en **Send**
   - ✅ El token se guardará automáticamente

**Nota**: Los scripts de test automáticamente guardan el token JWT en la variable `{{auth_token}}`. Todos los demás endpoints lo usarán automáticamente.

### Paso 2: Validar Token

- Endpoint: `Authentication > Validate Token`
- Verifica que tu token sea válido

### Paso 3: Probar Investments

#### Crear una inversión:
```json
POST /api/investments
{
    "timestamp": 1704067200000,
    "entidad": "Banco Nación",
    "monto_ars": 150000.50,
    "monto_usd": null
}
```

#### Crear múltiples inversiones:
```json
POST /api/investments/bulk
{
    "records": [
        {
            "timestamp": 1704067200000,
            "entidad": "Banco Nación",
            "monto_ars": 150000.50,
            "monto_usd": null
        },
        {
            "timestamp": 1704153600000,
            "entidad": "Mercado Pago",
            "monto_ars": 45000.00,
            "monto_usd": null
        }
    ]
}
```

#### Obtener todas las inversiones:
```
GET /api/investments
```

Filtros opcionales:
- `?entity=Banco Nación` - Filtrar por entidad
- `?dateFrom=1704067200000` - Desde fecha (timestamp)
- `?dateTo=1735689599000` - Hasta fecha (timestamp)
- `?limit=100&offset=0` - Paginación

#### Actualizar inversión:
```json
PUT /api/investments/:investment_id
{
    "monto_ars": 160000.00
}
```
**Nota**: Reemplaza `:investment_id` con el ID real obtenido de GET.

#### Eliminar inversión:
```
DELETE /api/investments/:investment_id
```

### Paso 4: Configurar Sitios Web

#### Crear configuración:
```json
POST /api/config/sites
{
    "name": "Banco Nación",
    "urlPattern": "https://hb.redlink.com.ar/*",
    "selectors": {
        "ars": ".saldo-total",
        "usd": null
    },
    "investment": "Plazo Fijo"
}
```

#### Obtener configuraciones:
```
GET /api/config/sites
```

### Paso 5: Preferencias de Usuario

#### Obtener preferencias:
```
GET /api/user/preferences
```

#### Actualizar preferencias:
```json
PUT /api/user/preferences
{
    "theme": "dark",
    "autoReplication": {
        "enabled": true,
        "entities": {
            "Banco Nación": true,
            "Mercado Pago": false
        }
    }
}
```

### Paso 6: Sincronización

#### Estado de sincronización:
```
GET /api/sync/status
```

#### Push (enviar datos al servidor):
```json
POST /api/sync/push
{
    "investments": [...],
    "configSites": [...],
    "preferences": {...},
    "clientTimestamp": "2024-01-15T12:00:00Z"
}
```

#### Pull (obtener datos del servidor):
```
GET /api/sync/pull
GET /api/sync/pull?since=1704067200000
```

### Paso 7: Export/Import

#### Exportar todos los datos:
```
GET /api/export
```
Guarda la respuesta para hacer backup.

#### Importar datos (merge):
```json
POST /api/import
{
    "data": {
        "investments": [...],
        "configSites": [...],
        "preferences": {...}
    },
    "mode": "merge"
}
```

#### Importar datos (replace):
```json
POST /api/import
{
    "data": {...},
    "mode": "replace"
}
```
⚠️ **Cuidado**: Mode "replace" elimina todos los datos existentes.

## 📊 Estructura de la Colección

```
Investment Tracker API/
├── Authentication
│   ├── Register User
│   ├── Login
│   └── Validate Token
├── Investments
│   ├── Get All Investments
│   ├── Create Investment
│   ├── Bulk Create Investments
│   ├── Update Investment
│   ├── Delete Investment
│   └── Delete All Investments
├── Config Sites
│   ├── Get All Config Sites
│   ├── Create Config Site
│   ├── Update Config Site
│   └── Delete Config Site
├── User Preferences
│   ├── Get Preferences
│   └── Update Preferences
├── Synchronization
│   ├── Get Sync Status
│   ├── Push Sync
│   └── Pull Sync
├── Export & Import
│   ├── Export All Data
│   ├── Import Data (Merge)
│   └── Import Data (Replace)
└── Health & Root
    ├── Root
    └── Health Check
```

## 🔧 Variables de Environment

Las siguientes variables se configuran automáticamente:

- `{{base_url}}` - URL base de la API (production o local)
- `{{auth_token}}` - Token JWT (se guarda automáticamente al hacer login/register)
- `{{user_id}}` - ID del usuario (se guarda automáticamente al hacer login/register)

## 💡 Tips

1. **Siempre empieza con Authentication**: Necesitas un token válido para todos los endpoints protegidos.

2. **Los tokens expiran en 7 días**: Si obtienes error 401, vuelve a hacer login.

3. **Copia los IDs**: Cuando crees recursos (investments, config sites), copia el `id` de la respuesta para usarlo en operaciones de update/delete.

4. **Usa los filtros de fecha**: Los timestamps están en milisegundos (JavaScript Date format).
   - Convertir fecha a timestamp: `new Date('2024-01-01').getTime()`
   - Convertir timestamp a fecha: `new Date(1704067200000)`

5. **Prueba primero en Local**: Si tienes el servidor corriendo localmente, usa el environment "Local" para probar.

6. **Scripts automáticos**: Los endpoints de Register y Login tienen scripts que automáticamente guardan el token. No necesitas copiarlo manualmente.

## 🐛 Troubleshooting

### Error 401 Unauthorized
- Tu token ha expirado o es inválido
- Solución: Ejecuta Login nuevamente

### Error 404 Not Found
- Verifica que la URL base sea correcta
- Verifica que el endpoint exista

### Error 400 Bad Request
- Revisa el formato del body
- Asegúrate de que todos los campos requeridos estén presentes

### Error 500 Internal Server Error
- Revisa los logs del servidor
- Verifica la conexión a MongoDB

## 📚 Documentación Adicional

- **Swagger UI**: https://assets-tracker-api.up.railway.app/docs
- **ReDoc**: https://assets-tracker-api.up.railway.app/redoc
- **GitHub**: https://github.com/josemqu/assets-tracker-api

---

**¿Preguntas o problemas?** Abre un issue en GitHub.
