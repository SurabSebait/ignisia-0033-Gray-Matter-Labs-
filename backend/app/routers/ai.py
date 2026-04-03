from fastapi import APIRouter
from app.models.ai_response import AIResponseRequest, AIResponse
from app.services.ai_service import AIService
from app.db.connection import get_database

router = APIRouter()

@router.post("/generate-response", response_model=AIResponse)
async def generate_response(request: AIResponseRequest):
    db = get_database()
    service = AIService(db)
    return await service.generate_response(request)