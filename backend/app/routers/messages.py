from fastapi import APIRouter, HTTPException, Depends
from app.models.message import MessageCreate, Message
from app.services.message_service import MessageService
from app.services.auth_service import get_current_user, get_current_user_optional, require_roles
from app.db.connection import get_database
from bson import ObjectId

router = APIRouter()

@router.post("/{ticket_id}/messages", response_model=Message)
async def create_message(ticket_id: str, message: MessageCreate, current_user: dict = Depends(get_current_user)):
    db = get_database()
    service = MessageService(db)
    
    # Check permissions
    if current_user["role"] == "user":
        # Users can only send to their own tickets
        ticket = await db.tickets.find_one({"_id": ObjectId(ticket_id), "user_id": current_user["user_id"]})
        if not ticket:
            raise HTTPException(status_code=403, detail="Not authorized to send message to this ticket")
        if message.sender_type != "user":
            raise HTTPException(status_code=400, detail="Users can only send user messages")
    else:
        # Support/admin can send agent messages
        if message.sender_type != "agent":
            raise HTTPException(status_code=400, detail="Support can only send agent messages")
    
    return await service.create_message(ticket_id, message)

@router.get("/{ticket_id}/messages", response_model=list[Message])
async def get_messages(ticket_id: str, current_user: dict = Depends(get_current_user_optional)):
    db = get_database()
    service = MessageService(db)
    
    # Check permissions if authenticated
    if current_user is not None:
        if current_user["role"] == "user":
            ticket = await db.tickets.find_one({"_id": ObjectId(ticket_id), "user_id": current_user["user_id"]})
            if not ticket:
                raise HTTPException(status_code=403, detail="Not authorized to view messages for this ticket")
    
    return await service.get_messages(ticket_id)