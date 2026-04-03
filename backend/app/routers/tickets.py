from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from app.models.ticket import TicketCreate, TicketUpdate, Ticket
from app.services.ticket_service import TicketService
from app.services.auth_service import get_current_user, get_current_user_optional, require_roles, require_role
from app.db.connection import get_database
from typing import List
from pydantic import BaseModel
from bson import ObjectId

class SimilarTicket(BaseModel):
    ticket_id: str
    query: str
    last_response: str
    similarity_score: float

router = APIRouter()

@router.post("/", response_model=Ticket, dependencies=[Depends(require_role("user"))])
async def create_ticket(ticket: TicketCreate, current_user: dict = Depends(get_current_user)):
    db = get_database()
    service = TicketService(db)
    # Override user_id with authenticated user's username
    ticket.user_id = current_user["username"]
    return await service.create_ticket(ticket)

@router.get("/", response_model=list[Ticket])
async def list_tickets(skip: int = 0, limit: int = 10, current_user: dict = Depends(get_current_user_optional)):
    db = get_database()
    service = TicketService(db)
    if current_user is None:
        # Return empty list for unauthenticated users
        return []
    if current_user["role"] == "user":
        # Users see only their tickets
        return await service.list_user_tickets(current_user["user_id"], skip, limit)
    else:
        # Support/admin see all
        return await service.list_tickets(skip, limit)

@router.get("/{ticket_id}", response_model=Ticket)
async def get_ticket(ticket_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    service = TicketService(db)
    ticket = await service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Check permissions
    if current_user["role"] == "user" and ticket.user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to view this ticket")
    
    return ticket

@router.patch("/{ticket_id}", response_model=Ticket, dependencies=[Depends(require_roles(["support", "admin"]))])
async def update_ticket(ticket_id: str, ticket_update: TicketUpdate, current_user: dict = Depends(get_current_user)):
    db = get_database()
    service = TicketService(db)
    ticket = await service.update_ticket(ticket_id, ticket_update)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@router.patch("/{ticket_id}/lock", response_model=Ticket, dependencies=[Depends(require_roles(["support", "admin"]))])
async def lock_ticket(ticket_id: str, agent_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    service = TicketService(db)
    return await service.lock_ticket(ticket_id, agent_id)

@router.patch("/{ticket_id}/unlock", response_model=Ticket, dependencies=[Depends(require_roles(["support", "admin"]))])
async def unlock_ticket(ticket_id: str, agent_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    service = TicketService(db)
    return await service.unlock_ticket(ticket_id, agent_id)

@router.get("/{ticket_id}/similar", response_model=List[SimilarTicket], dependencies=[Depends(require_roles(["support", "admin"]))])
async def get_similar_tickets(ticket_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    service = TicketService(db)
    ticket = await service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Simple similarity: find tickets with similar words (placeholder)
    query_words = set(ticket.query.lower().split())
    similar = []
    async for t in db.tickets.find({"_id": {"$ne": ObjectId(ticket_id)}}).limit(5):
        t_words = set(t["query"].lower().split())
        score = len(query_words & t_words) / len(query_words | t_words) if query_words | t_words else 0
        if score > 0.1:
            # Get last response
            last_msg = await db.messages.find_one({"ticket_id": str(t["_id"])}, sort=[("created_at", -1)])
            last_response = last_msg["message"] if last_msg else "No response yet"
            similar.append(SimilarTicket(
                ticket_id=str(t["_id"]),
                query=t["query"],
                last_response=last_response,
                similarity_score=round(score, 2)
            ))
    return sorted(similar, key=lambda x: x.similarity_score, reverse=True)