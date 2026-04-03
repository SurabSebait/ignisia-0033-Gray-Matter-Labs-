from pydantic import BaseModel
from datetime import datetime

class FileModel(BaseModel):
    id: str
    file_name: str
    file_type: str
    gcs_path: str
    processed: bool
    created_at: datetime

    class Config:
        orm_mode = True