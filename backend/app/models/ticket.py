from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TicketBase(BaseModel):
    user_id: str
    query: str
    status: Optional[str] = "open"
    priority: Optional[str] = "medium"

class TicketCreate(TicketBase):
    pass

class TicketUpdate(BaseModel):
    status: Optional[str]
    priority: Optional[str]

class Ticket(TicketBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True