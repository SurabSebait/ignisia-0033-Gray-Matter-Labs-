from fastapi import APIRouter, HTTPException, Depends
from app.models.file import FileCreate, FileModel, FileStatusUpdate
from app.services.file_service import FileService
from app.services.auth_service import require_role
from app.db.connection import get_database

router = APIRouter()

@router.post("/", response_model=FileModel, dependencies=[Depends(require_role("admin"))])
async def create_file(file: FileCreate):
    db = get_database()
    service = FileService(db)
    return await service.create_file(file)

@router.patch("/{file_id}/status", response_model=FileModel, dependencies=[Depends(require_role("admin"))])
async def update_file_status(file_id: str, status_update: FileStatusUpdate):
    db = get_database()
    service = FileService(db)
    file = await service.update_file_status(file_id, status_update)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file