from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.ai_response import AIResponseRequest, AIResponse, Citation
from app.services.message_service import MessageService

class AIService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def generate_response(self, request: AIResponseRequest) -> AIResponse:
        # Stub: Assume external RAG returns this
        response = "This is a generated AI response based on the query."
        citations = [
            Citation(
                text="Sample chunk text from PDF.",
                source_type="pdf",
                source_name="manual.pdf",
                reference="page 5",
                relevance_score=0.95
            )
        ]
        # Store in ai_responses
        ai_response_dict = {
            "ticket_id": request.ticket_id,
            "message_id": None,  # Will be set when message is created
            "response": response,
            "citations": [c.dict() for c in citations]
        }
        result = await self.db.ai_responses.insert_one(ai_response_dict)
        ai_response_dict["_id"] = str(result.inserted_id)
        return AIResponse(**ai_response_dict)