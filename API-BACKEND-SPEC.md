# 📡 API Backend Specification - Investment Tracker

**Versión:** 1.0  
**Fecha:** Enero 2025

---

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Arquitectura](#arquitectura)
3. [Estructura de Datos](#estructura-de-datos)
4. [Endpoints API](#endpoints-api)
5. [Autenticación](#autenticación)
6. [Base de Datos](#base-de-datos)
7. [Integración con la Extensión](#integración-con-la-extensión)
8. [Despliegue](#despliegue)

---

## 🎯 Introducción

Backend centralizado para la extensión Chrome Investment Tracker que permite:

- ✅ Sincronización multi-dispositivo
- ✅ Backup automático en la nube
- ✅ Almacenamiento ilimitado
- ✅ Análisis avanzado de datos

### Estado Actual de la Extensión

- **chrome.storage.local**: trackerData (registros de inversiones)
- **chrome.storage.sync**: configSites (configuración de sitios) + preferencias

---

## 🏗️ Arquitectura

```
Chrome Extension (Frontend)
    ↓ HTTPS/REST
Backend API (Python + FastAPI)
    ↓
Database (MongoDB Atlas)
```

### Stack Tecnológico

- **Backend**: Python 3.11+ + FastAPI
- **Database**: MongoDB Atlas
- **Auth**: JWT (JSON Web Tokens)
- **ODM**: Motor (async MongoDB driver)
- **Validation**: Pydantic
- **Hosting**: Railway / Render / Fly.io
- **CORS**: Configurado para extensión Chrome

---

## 📊 Estructura de Datos

### 1. Investment Record

```typescript
{
  id: string; // ID backend
  userId: string; // ID del usuario
  timestamp: number; // Milisegundos
  entidad: string; // Nombre del banco
  monto_ars: number | null;
  monto_usd: number | null;
  createdAt: Date;
  updatedAt: Date;
}
```

**Regla única**: Un registro por día por entidad (timestamp + entidad)

### 2. Site Configuration

```typescript
{
  id: string;
  userId: string;
  name: string;            // "Banco Nación"
  urlPattern: string;      // "https://banco.com/*"
  selectors: {
    ars?: string;          // Selector CSS
    usd?: string;
  };
  investment: string;      // "Plazo Fijo"
  createdAt: Date;
  updatedAt: Date;
}
```

### 3. User

```typescript
{
  id: string;
  email: string;
  passwordHash: string;    // Bcrypt
  name?: string;
  createdAt: Date;
  lastLogin?: Date;
  preferences?: {
    theme?: 'light' | 'dark';
    autoReplication?: {
      enabled: boolean;
      entities: Record<string, boolean>;
    };
    manualRecordReferences?: Record<string, any>;
  };
}
```

---

## 🔌 Endpoints API

**Base URL**:

- Dev: `http://localhost:8000/api`
- Prod: `https://your-app.com/api`

### Autenticación

#### `POST /api/auth/register`

```json
Request: { "email": "user@example.com", "password": "pass123", "name": "User" }
Response: { "success": true, "data": { "userId": "123", "token": "jwt..." } }
```

#### `POST /api/auth/login`

```json
Request: { "email": "user@example.com", "password": "pass123" }
Response: { "success": true, "data": { "userId": "123", "token": "jwt..." } }
```

#### `GET /api/auth/validate`

```
Headers: Authorization: Bearer {token}
Response: { "success": true, "data": { "valid": true, "userId": "123" } }
```

---

### Inversiones (Investments)

#### `GET /api/investments`

Obtener todos los registros del usuario

```
Headers: Authorization: Bearer {token}
Query: ?entity=Banco&dateFrom=2024-01-01&dateTo=2024-01-31&limit=1000&offset=0

Response: {
  "success": true,
  "data": [ {...}, {...} ],
  "pagination": { "total": 150, "limit": 1000, "offset": 0 }
}
```

#### `POST /api/investments`

Crear o actualizar registro

```json
Headers: Authorization: Bearer {token}
Request: {
  "timestamp": 1704067200000,
  "entidad": "Banco Nación",
  "monto_ars": 150000.50,
  "monto_usd": null
}

Response: {
  "success": true,
  "data": { "id": "abc123", ... },
  "isUpdate": false
}
```

#### `POST /api/investments/bulk`

Sincronización masiva

```json
Headers: Authorization: Bearer {token}
Request: {
  "records": [
    { "timestamp": 1704067200000, "entidad": "Banco", "monto_ars": 150000 },
    { "timestamp": 1704153600000, "entidad": "Mercado Pago", "monto_ars": 45000 }
  ]
}

Response: {
  "success": true,
  "summary": { "total": 2, "created": 1, "updated": 1, "failed": 0 }
}
```

#### `PUT /api/investments/:id`

Actualizar registro específico

```json
Headers: Authorization: Bearer {token}
Request: { "monto_ars": 151000.00 }
Response: { "success": true, "data": { ... } }
```

#### `DELETE /api/investments/:id`

Eliminar registro

```
Headers: Authorization: Bearer {token}
Response: { "success": true }
```

#### `DELETE /api/investments`

Eliminar todos los registros

```
Headers: Authorization: Bearer {token}
Response: { "success": true, "deleted": 50 }
```

---

### Configuración de Sitios

#### `GET /api/config/sites`

```
Headers: Authorization: Bearer {token}
Response: { "success": true, "data": [ {...}, {...} ] }
```

#### `POST /api/config/sites`

```json
Headers: Authorization: Bearer {token}
Request: {
  "name": "Banco Nación",
  "urlPattern": "https://hb.redlink.com.ar/*",
  "selectors": { "ars": ".saldo-total" },
  "investment": "Plazo Fijo"
}
Response: { "success": true, "data": { "id": "cfg123", ... } }
```

#### `PUT /api/config/sites/:id`

```json
Headers: Authorization: Bearer {token}
Request: { "selectors": { "ars": ".new-selector" } }
Response: { "success": true, "data": { ... } }
```

#### `DELETE /api/config/sites/:id`

```
Headers: Authorization: Bearer {token}
Response: { "success": true }
```

---

### Preferencias

#### `GET /api/user/preferences`

```
Headers: Authorization: Bearer {token}
Response: { "success": true, "data": { "theme": "dark", ... } }
```

#### `PUT /api/user/preferences`

```json
Headers: Authorization: Bearer {token}
Request: { "theme": "light", "autoReplication": { "enabled": false } }
Response: { "success": true, "data": { ... } }
```

---

### Sincronización

#### `GET /api/sync/status`

```
Headers: Authorization: Bearer {token}
Response: {
  "success": true,
  "data": {
    "lastSync": "2024-01-15T12:00:00Z",
    "recordCount": 50,
    "configCount": 5
  }
}
```

#### `POST /api/sync/push`

Enviar cambios locales al servidor

```json
Headers: Authorization: Bearer {token}
Request: {
  "investments": [ {...} ],
  "configSites": [ {...} ],
  "preferences": { ... },
  "clientTimestamp": "2024-01-15T12:00:00Z"
}

Response: {
  "success": true,
  "synced": {
    "investments": { "created": 1, "updated": 0 },
    "configSites": { "created": 0, "updated": 1 }
  },
  "serverTimestamp": "2024-01-15T12:00:05Z"
}
```

#### `GET /api/sync/pull`

Obtener cambios desde el servidor

```
Headers: Authorization: Bearer {token}
Query: ?since=1704067200000

Response: {
  "success": true,
  "data": {
    "investments": [ {...} ],
    "configSites": [ {...} ],
    "preferences": { ... },
    "deletedInvestments": ["id1"],
    "deletedConfigSites": ["id2"]
  },
  "serverTimestamp": "2024-01-15T12:00:05Z"
}
```

---

### Export/Import

#### `GET /api/export`

Exportar todos los datos

```
Headers: Authorization: Bearer {token}
Response: {
  "version": "1.0",
  "exportDate": "2024-01-15T12:00:00Z",
  "user": { "email": "..." },
  "data": {
    "investments": [ {...} ],
    "configSites": [ {...} ],
    "preferences": { ... }
  }
}
```

#### `POST /api/import`

Importar datos

```json
Headers: Authorization: Bearer {token}
Request: {
  "data": { "investments": [...], "configSites": [...] },
  "mode": "replace"
}
Response: {
  "success": true,
  "imported": { "investments": 50, "configSites": 5 }
}
```

---

## 🔐 Autenticación

### JWT Configuration

```python
{
  "algorithm": "HS256",
  "expires_delta": timedelta(days=7),
  "secret": os.getenv("JWT_SECRET")
}
```

### Security Headers

```
Authorization: Bearer {token}
Content-Type: application/json
```

### Rate Limiting

- 100 requests/min por IP
- 1000 requests/hora por usuario

### CORS

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://YOUR_EXTENSION_ID"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

---

## 💾 Base de Datos

### MongoDB Atlas

#### Collections & Indexes

**users**

```python
{
  "_id": ObjectId,
  "email": str (unique, indexed),
  "password_hash": str,
  "name": str,
  "preferences": dict,
  "created_at": datetime,
  "last_login": datetime
}

await db.users.create_index([("email", 1)], unique=True)
```

**investments**

```python
{
  "_id": ObjectId,
  "user_id": ObjectId (indexed),
  "timestamp": int (indexed),
  "entidad": str (indexed),
  "monto_ars": float | None,
  "monto_usd": float | None,
  "created_at": datetime,
  "updated_at": datetime
}

# Índice único compuesto
await db.investments.create_index(
    [("user_id", 1), ("timestamp", 1), ("entidad", 1)],
    unique=True
)

# Índices de consulta
await db.investments.create_index([("user_id", 1), ("timestamp", -1)])
await db.investments.create_index([("user_id", 1), ("entidad", 1)])
```

**config_sites**

```python
{
  "_id": ObjectId,
  "user_id": ObjectId (indexed),
  "name": str,
  "url_pattern": str,
  "selectors": dict,
  "investment": str,
  "created_at": datetime,
  "updated_at": datetime
}

await db.config_sites.create_index([("user_id", 1)])
```

**sync_logs** (opcional)

```python
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "timestamp": datetime,
  "action": str,
  "records_affected": int,
  "success": bool
}

# TTL index - expira en 30 días
await db.sync_logs.create_index(
    [("timestamp", 1)],
    expireAfterSeconds=2592000
)
```

---

## 🔗 Integración con la Extensión

### 1. Crear API Client en la Extensión

**Archivo**: `utils/api-client.js`

```javascript
class APIClient {
  constructor(baseURL) {
    this.baseURL = baseURL;
    this.token = null;
  }

  async setToken(token) {
    this.token = token;
    await chrome.storage.local.set({ apiToken: token });
  }

  async getToken() {
    if (this.token) return this.token;
    const { apiToken } = await chrome.storage.local.get("apiToken");
    this.token = apiToken;
    return apiToken;
  }

  async request(endpoint, options = {}) {
    const token = await this.getToken();
    const headers = {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    };

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      // Token inválido - limpiar y requerir login
      await this.logout();
      throw new Error("Sesión expirada");
    }

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Error en la petición");
    }

    return data;
  }

  // Auth
  async register(email, password, name) {
    const data = await this.request("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, name }),
    });
    await this.setToken(data.data.token);
    return data;
  }

  async login(email, password) {
    const data = await this.request("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    await this.setToken(data.data.token);
    return data;
  }

  async logout() {
    try {
      await this.request("/api/auth/logout", { method: "POST" });
    } catch (e) {
      // Ignorar errores en logout
    } finally {
      this.token = null;
      await chrome.storage.local.remove("apiToken");
    }
  }

  async validateToken() {
    try {
      return await this.request("/api/auth/validate");
    } catch (e) {
      return { success: false, data: { valid: false } };
    }
  }

  // Investments
  async getInvestments(filters = {}) {
    const params = new URLSearchParams(filters).toString();
    return this.request(`/api/investments?${params}`);
  }

  async createInvestment(record) {
    return this.request("/api/investments", {
      method: "POST",
      body: JSON.stringify(record),
    });
  }

  async bulkCreateInvestments(records) {
    return this.request("/api/investments/bulk", {
      method: "POST",
      body: JSON.stringify({ records }),
    });
  }

  async updateInvestment(id, updates) {
    return this.request(`/api/investments/${id}`, {
      method: "PUT",
      body: JSON.stringify(updates),
    });
  }

  async deleteInvestment(id) {
    return this.request(`/api/investments/${id}`, {
      method: "DELETE",
    });
  }

  async deleteAllInvestments() {
    return this.request("/api/investments", {
      method: "DELETE",
    });
  }

  // Config Sites
  async getConfigSites() {
    return this.request("/api/config/sites");
  }

  async createConfigSite(config) {
    return this.request("/api/config/sites", {
      method: "POST",
      body: JSON.stringify(config),
    });
  }

  async updateConfigSite(id, updates) {
    return this.request(`/api/config/sites/${id}`, {
      method: "PUT",
      body: JSON.stringify(updates),
    });
  }

  async deleteConfigSite(id) {
    return this.request(`/api/config/sites/${id}`, {
      method: "DELETE",
    });
  }

  // Preferences
  async getPreferences() {
    return this.request("/api/user/preferences");
  }

  async updatePreferences(preferences) {
    return this.request("/api/user/preferences", {
      method: "PUT",
      body: JSON.stringify(preferences),
    });
  }

  // Sync
  async getSyncStatus() {
    return this.request("/api/sync/status");
  }

  async pushSync(data) {
    return this.request("/api/sync/push", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async pullSync(since) {
    const params = since ? `?since=${since}` : "";
    return this.request(`/api/sync/pull${params}`);
  }

  // Export/Import
  async exportData() {
    return this.request("/api/export");
  }

  async importData(data, mode = "merge") {
    return this.request("/api/import", {
      method: "POST",
      body: JSON.stringify({ data, mode }),
    });
  }
}

// Instancia global
const apiClient = new APIClient(
  process.env.NODE_ENV === "production"
    ? "https://your-app.com"
    : "http://localhost:3000"
);

window.apiClient = apiClient;
```

---

### 2. Modificar background.js

```javascript
// Al capturar datos nuevos, sincronizar con backend
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "storeData") {
    // Guardar localmente primero
    const newRecord = {
      timestamp: message.data.timestamp,
      entidad: message.data.entidad,
      monto_ars: cleanAmount(message.data.monto_ars),
      monto_usd: cleanAmount(message.data.monto_usd),
    };

    // Guardar en chrome.storage.local
    appendTrackerRecord(newRecord).then(async () => {
      // Si está autenticado, sincronizar con backend
      const token = await apiClient.getToken();
      if (token) {
        try {
          await apiClient.createInvestment(newRecord);
          console.log("✅ Sincronizado con backend");
        } catch (error) {
          console.error("❌ Error sincronizando con backend:", error);
          // Continuar - el dato ya está guardado localmente
        }
      }

      sendResponse({ success: true });
    });

    return true;
  }
});
```

---

### 3. Agregar UI de Login en popup.html

```html
<!-- Login Modal -->
<div class="modal fade" id="loginModal" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Iniciar Sesión</h5>
        <button
          type="button"
          class="btn-close"
          data-bs-dismiss="modal"
        ></button>
      </div>
      <div class="modal-body">
        <form id="loginForm">
          <div class="mb-3">
            <label for="loginEmail" class="form-label">Email</label>
            <input type="email" class="form-control" id="loginEmail" required />
          </div>
          <div class="mb-3">
            <label for="loginPassword" class="form-label">Contraseña</label>
            <input
              type="password"
              class="form-control"
              id="loginPassword"
              required
            />
          </div>
          <button type="submit" class="btn btn-primary w-100">
            Iniciar Sesión
          </button>
        </form>
        <div class="mt-3 text-center">
          <small
            >¿No tienes cuenta?
            <a href="#" id="showRegister">Regístrate</a></small
          >
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Botón de Sync en header -->
<button id="syncButton" class="btn btn-outline-primary btn-sm">
  <i class="bi bi-cloud-arrow-up"></i>
  <span id="syncStatus">Sincronizar</span>
</button>
```

---

### 4. Funciones de Sincronización en popup.js

```javascript
// Verificar autenticación al cargar
document.addEventListener("DOMContentLoaded", async () => {
  const { valid } = await apiClient.validateToken();

  if (valid) {
    document.getElementById("syncStatus").textContent = "Conectado";
    document.getElementById("syncButton").classList.add("btn-success");
  } else {
    document.getElementById("syncStatus").textContent = "Sin conexión";
  }
});

// Sincronización completa
async function fullSync() {
  try {
    // 1. Obtener datos locales
    const localInvestments = await loadTrackerData();
    const localConfigs = await storageGet(["configSites"]);

    // 2. Push a backend
    await apiClient.pushSync({
      investments: localInvestments,
      configSites: localConfigs.configSites || [],
      clientTimestamp: new Date().toISOString(),
    });

    // 3. Pull desde backend
    const serverData = await apiClient.pullSync();

    // 4. Merge datos
    if (serverData.data.investments.length > 0) {
      await saveTrackerData(serverData.data.investments);
    }

    if (serverData.data.configSites.length > 0) {
      await storageSet({ configSites: serverData.data.configSites });
    }

    console.log("✅ Sincronización completa");
    alert("Sincronización exitosa");
  } catch (error) {
    console.error("Error en sincronización:", error);
    alert("Error al sincronizar: " + error.message);
  }
}

document.getElementById("syncButton").addEventListener("click", fullSync);
```

---

## 🚀 Despliegue

### Variables de Entorno

```env
# .env
ENVIRONMENT=production
PORT=8000

# JWT
JWT_SECRET=your-super-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=7

# MongoDB
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/investment-tracker?retryWrites=true&w=majority

# CORS
ALLOWED_ORIGINS=chrome-extension://your-extension-id

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
```

---

### Deployment en Railway/Render

**Railway:**

1. **Crear cuenta** en railway.app
2. **Nuevo proyecto** → Deploy from GitHub
3. **Agregar variables** de entorno
4. **Conectar MongoDB** Atlas
5. **Deploy** automático

**Render:**

1. **Crear cuenta** en render.com
2. **New Web Service** → Connect GitHub repo
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. **Agregar variables** de entorno

**URL final**: `https://your-app.railway.app` o `https://your-app.onrender.com`

---

### Actualizar Extensión

```javascript
// utils/api-client.js
const apiClient = new APIClient('https://your-app.railway.app');
// o
const apiClient = new APIClient('https://your-app.onrender.com');
```

```json
// manifest.json
{
  "host_permissions": [
    "https://your-app.railway.app/*",
    "https://your-app.onrender.com/*"
  ]
}
```

---

## 📝 Checklist de Implementación

### Backend

- [ ] Crear proyecto FastAPI + Python 3.11+
- [ ] Configurar MongoDB Atlas con Motor
- [ ] Implementar modelos Pydantic
- [ ] Implementar rutas de autenticación
- [ ] Implementar rutas de inversiones
- [ ] Implementar rutas de config sites
- [ ] Implementar sincronización
- [ ] Configurar JWT y seguridad
- [ ] Agregar rate limiting con slowapi
- [ ] Configurar CORS
- [ ] Deploy en Railway/Render

### Extensión

- [ ] Crear `utils/api-client.js`
- [ ] Agregar UI de login/registro
- [ ] Modificar background.js para sync automático
- [ ] Agregar botón de sincronización manual
- [ ] Implementar merge inteligente de datos
- [ ] Manejar conflictos de sincronización
- [ ] Agregar indicadores de estado
- [ ] Actualizar manifest.json con permisos
- [ ] Testing de integración
- [ ] Deploy de extensión actualizada

---

## 🔍 Testing

```bash
# Probar endpoint de registro
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","name":"Test User"}'

# Probar creación de inversión
curl -X POST http://localhost:8000/api/investments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"timestamp":1704067200000,"entidad":"Banco","monto_ars":150000}'

# Ver documentación interactiva
open http://localhost:8000/docs
```

---

## 📚 Recursos Adicionales

- **FastAPI**: <https://fastapi.tiangolo.com/>
- **Motor (async MongoDB)**: <https://motor.readthedocs.io/>
- **Pydantic**: <https://docs.pydantic.dev/>
- **MongoDB Atlas**: <https://www.mongodb.com/cloud/atlas>
- **JWT**: <https://jwt.io/>
- **Railway**: <https://railway.app/>
- **Render**: <https://render.com/>
- **Chrome Extension API**: <https://developer.chrome.com/docs/extensions/>

---

**Autor**: Investment Tracker Team  
**Última actualización**: Enero 2025
