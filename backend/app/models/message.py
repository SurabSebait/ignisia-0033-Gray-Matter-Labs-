from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MessageBase(BaseModel):
    sender_type: str  # user/agent/ai
    message: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: str
    ticket_id: str
    created_at: datetime
    edited: bool

    class Config:
        from_attributes = True