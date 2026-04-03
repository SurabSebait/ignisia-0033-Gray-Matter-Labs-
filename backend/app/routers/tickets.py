from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from app.models.ticket import TicketCreate, TicketUpdate, Ticket
from app.services.ticket_service import TicketService
from app.db.connection import get_database

router = APIRouter()

@router.post("/", response_model=Ticket)
async def create_ticket(ticket: TicketCreate):
    db = get_database()
    service = TicketService(db)
    return await service.create_ticket(ticket)

@router.get("/", response_model=list[Ticket])
async def list_tickets(skip: int = 0, limit: int = 10):
    db = get_database()
    service = TicketService(db)
    return await service.list_tickets(skip, limit)

@router.get("/{ticket_id}", response_model=Ticket)
async def get_ticket(ticket_id: str):
    db = get_database()
    service = TicketService(db)
    ticket = await service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@router.patch("/{ticket_id}", response_model=Ticket)
async def update_ticket(ticket_id: str, ticket_update: TicketUpdate):
    db = get_database()
    service = TicketService(db)
    ticket = await service.update_ticket(ticket_id, ticket_update)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket