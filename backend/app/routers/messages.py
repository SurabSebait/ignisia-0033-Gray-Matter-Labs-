from fastapi import APIRouter, HTTPException
from app.models.message import MessageCreate, Message
from app.services.message_service import MessageService
from app.db.connection import get_database

router = APIRouter()

@router.post("/{ticket_id}/messages", response_model=Message)
async def create_message(ticket_id: str, message: MessageCreate):
    db = get_database()
    service = MessageService(db)
    return await service.create_message(ticket_id, message)

@router.get("/{ticket_id}/messages", response_model=list[Message])
async def get_messages(ticket_id: str):
    db = get_database()
    service = MessageService(db)
    return await service.get_messages(ticket_id)