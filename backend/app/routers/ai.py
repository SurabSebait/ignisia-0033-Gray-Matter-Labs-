from fastapi import APIRouter, Depends
from app.models.ai_response import AIResponseRequest, AIResponse
from app.services.ai_service import AIService
from app.services.auth_service import require_roles
from app.db.connection import get_database
from app.config.settings import settings

router = APIRouter()

@router.post("/generate-response", response_model=AIResponse, dependencies=[Depends(require_roles(["support", "admin"]))])
async def generate_response(request: AIResponseRequest):
    db = get_database()
    service = AIService(db)

    # Env-driven demo values available for future extension
    api_key = settings.openai_api_key
    model_name = settings.ai_model
    # If ai_service_url is set, route to external AI service in future

    return await service.generate_response(request)