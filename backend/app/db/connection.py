from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings

client: AsyncIOMotorClient = None
db = None

async def connect_to_mongo():
    global client, db
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.database_name]

async def close_mongo_connection():
    global client
    if client:
        client.close()

def get_database():
    return db