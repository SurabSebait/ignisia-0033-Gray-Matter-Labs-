from fastapi import APIRouter, HTTPException
from app.models.user import UserCreate, User, LoginRequest, LoginResponse
from app.services.auth_service import AuthService
from app.db.connection import get_database

router = APIRouter()

@router.post("/register", response_model=User)
async def register(user: UserCreate):
    db = get_database()
    service = AuthService(db)
    return await service.create_user(user)

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    db = get_database()
    service = AuthService(db)
    try:
        return await service.login(request)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid credentials")