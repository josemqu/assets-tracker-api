from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client: AsyncIOMotorClient = None
db = None


async def connect_to_mongo():
    global client, db
    try:
        print(f"🔌 Connecting to MongoDB...")
        client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client["investment-tracker"]  # Especificar nombre de base de datos explícitamente
        
        # Test connection
        await client.admin.command('ping')
        print(f"✅ MongoDB connected successfully to database: investment-tracker")
        
        # Crear índices
        await db.users.create_index("email", unique=True)
        await db.investments.create_index(
            [("user_id", 1), ("timestamp", 1), ("entidad", 1)],
            unique=True
        )
        await db.investments.create_index([("user_id", 1), ("timestamp", -1)])
        await db.investments.create_index([("user_id", 1), ("entidad", 1)])
        await db.config_sites.create_index([("user_id", 1)])
        print("✅ Database indexes created")
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        db = None
        raise


async def close_mongo_connection():
    global client
    if client:
        client.close()


def get_database():
    return db
