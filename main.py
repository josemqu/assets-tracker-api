from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import auth, investments, config, sync


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    print("🚀 Investment Tracker API started")
    yield
    # Shutdown
    await close_mongo_connection()
    print("👋 Investment Tracker API stopped")


app = FastAPI(
    title="Investment Tracker API",
    description="API Backend for Chrome Extension Investment Tracker",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(investments.router, prefix="/api/investments", tags=["Investments"])
app.include_router(config.router, prefix="/api/config", tags=["Configuration"])
app.include_router(config.router, prefix="/api/user", tags=["User"])
app.include_router(sync.router, prefix="/api/sync", tags=["Synchronization"])
app.include_router(sync.router, prefix="/api", tags=["Export/Import"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "Investment Tracker API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "OK",
        "environment": settings.ENVIRONMENT
    }
