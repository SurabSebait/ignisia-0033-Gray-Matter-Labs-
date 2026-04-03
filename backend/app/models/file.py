from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FileModel(BaseModel):
    id: str
    file_name: str
    file_type: str
    gcs_path: str
    status: str = "uploaded"  # uploaded, processing, completed, failed
    error_message: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class FileCreate(BaseModel):
    file_name: str
    file_type: str
    gcs_path: str

class FileStatusUpdate(BaseModel):
    status: str
    error_message: Optional[str] = None