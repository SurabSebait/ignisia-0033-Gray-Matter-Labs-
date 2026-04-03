from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings

client: AsyncIOMotorClient = None
db = None

async def connect_to_mongo():
    global client, db
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.database_name]
    
    # Create indexes
    await db.tickets.create_index("status")
    await db.tickets.create_index("assigned_to")
    await db.tickets.create_index("created_at")
    await db.tickets.create_index("locked_by")
    
    await db.messages.create_index([("ticket_id", 1), ("created_at", 1)])
    
    await db.ai_responses.create_index("ticket_id")
    
    await db.files.create_index("status")
    await db.files.create_index("created_at")

async def close_mongo_connection():
    global client
    if client:
        client.close()

def get_database():
    return db