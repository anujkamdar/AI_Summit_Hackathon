from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI")
db_client: Optional[AsyncIOMotorClient] = None
db = None


def get_db():
    """Get database instance"""
    return db


async def connect_db():
    """Connect to MongoDB"""
    global db_client, db
    if not MONGO_URI:
        raise ValueError("MONGO_URI not found in environment variables")
    
    db_client = AsyncIOMotorClient(MONGO_URI)
    db = db_client["job_agent_db"]


async def disconnect_db():
    """Disconnect from MongoDB"""
    global db_client
    if db_client:
        db_client.close()
