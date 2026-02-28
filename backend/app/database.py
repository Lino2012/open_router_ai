from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from beanie import init_beanie
from typing import Optional, Any

from .config import get_settings
from .models import User, Session, Message, MemoryEntry, UserPreferences
from .cache import cache

settings = get_settings()

# MongoDB client
class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

mongodb = MongoDB()

async def connect_to_mongo():
    """Create MongoDB connection"""
    try:
        mongo_url = settings.MONGODB_URL
        
        mongodb.client = AsyncIOMotorClient(
            mongo_url,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000
        )
        
        # Test the connection
        await mongodb.client.admin.command('ping')
        print("✅ MongoDB connection test successful")
        
        mongodb.db = mongodb.client[settings.MONGODB_DB_NAME]
        
        # Initialize Beanie with document models
        await init_beanie(
            database=mongodb.db,
            document_models=[User, Session, Message, MemoryEntry, UserPreferences]
        )
        
        # Create indexes
        await create_indexes()
        
        print("✅ Connected to MongoDB")
        return mongodb.db
        
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        raise e

async def close_mongo_connection():
    """Close MongoDB connection"""
    if mongodb.client:
        mongodb.client.close()
        print("Closed MongoDB connection")

async def create_indexes():
    """Create necessary indexes"""
    try:
        # User indexes
        await User.get_motor_collection().create_index("email", unique=True)
        await User.get_motor_collection().create_index("username", unique=True)
        
        # Session indexes
        session_collection = Session.get_motor_collection()
        await session_collection.create_index([("user_id", 1), ("created_at", -1)])  # type: ignore
        
        # Message indexes
        message_collection = Message.get_motor_collection()
        await message_collection.create_index([("session_id", 1), ("created_at", 1)])  # type: ignore
        
        # Memory indexes
        memory_collection = MemoryEntry.get_motor_collection()
        await memory_collection.create_index([("user_id", 1), ("created_at", -1)])  # type: ignore
        await memory_collection.create_index([("user_id", 1), ("type", 1)])  # type: ignore
        
        print("✅ Indexes created successfully")
    except Exception as e:
        print(f"⚠️ Index creation warning: {e}")

async def get_db():
    """Get database instance"""
    return mongodb.db