from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client: AsyncIOMotorClient = None
db = None


async def connect_to_mongo():
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client["investment-tracker"]  # Especificar nombre de base de datos explícitamente
    
    # Crear índices
    await db.users.create_index("email", unique=True)
    await db.investments.create_index(
        [("user_id", 1), ("timestamp", 1), ("entidad", 1)],
        unique=True
    )
    await db.investments.create_index([("user_id", 1), ("timestamp", -1)])
    await db.investments.create_index([("user_id", 1), ("entidad", 1)])
    await db.config_sites.create_index([("user_id", 1)])
    
    print("✅ MongoDB connected")


async def close_mongo_connection():
    global client
    if client:
        client.close()


def get_database():
    return db
