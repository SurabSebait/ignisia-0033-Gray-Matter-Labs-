from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.ticket import TicketCreate, TicketUpdate, Ticket
from datetime import datetime, timedelta
from bson import ObjectId
from fastapi import HTTPException

class TicketService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.tickets

    async def create_ticket(self, ticket: TicketCreate) -> Ticket:
        ticket_dict = ticket.dict()
        ticket_dict["created_at"] = datetime.utcnow()
        ticket_dict["updated_at"] = datetime.utcnow()
        ticket_dict["status"] = "open"
        result = await self.collection.insert_one(ticket_dict)
        ticket_dict["id"] = str(result.inserted_id)
        ticket_dict.pop("_id", None)  # Remove _id if it exists
        return Ticket(**ticket_dict)

    async def list_tickets(self, skip: int, limit: int) -> list[Ticket]:
        tickets = []
        async for ticket in self.collection.find().skip(skip).limit(limit):
            ticket["id"] = str(ticket["_id"])
            ticket.pop("_id", None)
            tickets.append(Ticket(**ticket))
        return tickets

    async def list_user_tickets(self, user_id: str, skip: int, limit: int) -> list[Ticket]:
        tickets = []
        async for ticket in self.collection.find({"user_id": user_id}).skip(skip).limit(limit):
            ticket["id"] = str(ticket["_id"])
            ticket.pop("_id", None)
            tickets.append(Ticket(**ticket))
        return tickets

    async def get_ticket(self, ticket_id: str) -> Ticket:
        ticket = await self.collection.find_one({"_id": ObjectId(ticket_id)})
        if ticket:
            ticket["id"] = str(ticket["_id"])
            ticket.pop("_id", None)
            return Ticket(**ticket)
        return None

    async def update_ticket(self, ticket_id: str, update: TicketUpdate) -> Ticket:
        update_dict = update.dict(exclude_unset=True)
        update_dict["updated_at"] = datetime.utcnow()
        result = await self.collection.update_one(
            {"_id": ObjectId(ticket_id)}, {"$set": update_dict}
        )
        if result.modified_count:
            return await self.get_ticket(ticket_id)
        return None

    async def lock_ticket(self, ticket_id: str, agent_id: str) -> Ticket:
        ticket = await self.get_ticket(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        now = datetime.utcnow()
        # Check if locked by another agent and not expired
        if ticket.locked_by and ticket.locked_by != agent_id:
            if ticket.locked_at and (now - ticket.locked_at) < timedelta(minutes=5):
                raise HTTPException(status_code=409, detail="Ticket locked by another agent")
        
        update_dict = {
            "locked_by": agent_id,
            "locked_at": now,
            "updated_at": now
        }
        result = await self.collection.update_one(
            {"_id": ObjectId(ticket_id)}, {"$set": update_dict}
        )
        if result.modified_count:
            return await self.get_ticket(ticket_id)
        return None

    async def unlock_ticket(self, ticket_id: str, agent_id: str) -> Ticket:
        ticket = await self.get_ticket(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        if ticket.locked_by != agent_id:
            raise HTTPException(status_code=403, detail="Not authorized to unlock")
        
        update_dict = {
            "locked_by": None,
            "locked_at": None,
            "updated_at": datetime.utcnow()
        }
        result = await self.collection.update_one(
            {"_id": ObjectId(ticket_id)}, {"$set": update_dict}
        )
        if result.modified_count:
            return await self.get_ticket(ticket_id)
        return None