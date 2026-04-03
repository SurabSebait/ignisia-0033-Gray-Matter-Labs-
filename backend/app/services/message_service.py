from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.message import MessageCreate, Message
from datetime import datetime
from bson import ObjectId

class MessageService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.messages

    async def create_message(self, ticket_id: str, message: MessageCreate) -> Message:
        message_dict = message.dict()
        message_dict["ticket_id"] = ticket_id
        message_dict["created_at"] = datetime.utcnow()
        message_dict["edited"] = False
        result = await self.collection.insert_one(message_dict)
        message_dict["_id"] = str(result.inserted_id)
        return Message(**message_dict)

    async def get_messages(self, ticket_id: str) -> list[Message]:
        messages = []
        async for message in self.collection.find({"ticket_id": ticket_id}):
            message["_id"] = str(message["_id"])
            messages.append(Message(**message))
        return messages