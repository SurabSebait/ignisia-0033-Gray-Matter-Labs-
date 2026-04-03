from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.file import FileCreate, FileModel, FileStatusUpdate
from datetime import datetime
from bson import ObjectId

class FileService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.files

    async def create_file(self, file: FileCreate) -> FileModel:
        file_dict = file.dict()
        file_dict["created_at"] = datetime.utcnow()
        file_dict["status"] = "uploaded"
        result = await self.collection.insert_one(file_dict)
        file_dict["id"] = str(result.inserted_id)
        return FileModel(**file_dict)

    async def update_file_status(self, file_id: str, status_update: FileStatusUpdate) -> FileModel:
        update_dict = status_update.dict(exclude_unset=True)
        if status_update.status in ["completed", "failed"]:
            update_dict["processed_at"] = datetime.utcnow()
        result = await self.collection.update_one(
            {"_id": ObjectId(file_id)}, {"$set": update_dict}
        )
        if result.modified_count:
            return await self.get_file(file_id)
        return None

    async def get_file(self, file_id: str) -> FileModel:
        file = await self.collection.find_one({"_id": ObjectId(file_id)})
        if file:
            file["id"] = str(file["_id"])
            return FileModel(**file)
        return None