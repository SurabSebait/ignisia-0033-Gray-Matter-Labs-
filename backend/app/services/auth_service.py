from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.user import UserCreate, User, LoginRequest, LoginResponse
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.config.settings import settings
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.db.connection import get_database

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=True)
security_optional = HTTPBearer(auto_error=False)

class AuthService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.users
        self.secret_key = "your-secret-key"  # In production, use settings

    def verify_password(self, plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password):
        return pwd_context.hash(password)

    async def create_user(self, user: UserCreate) -> User:
        user_dict = user.dict()
        user_dict["password"] = self.get_password_hash(user.password)
        result = await self.collection.insert_one(user_dict)
        user_dict["id"] = str(result.inserted_id)
        del user_dict["_id"]
        return User(**{k: v for k, v in user_dict.items() if k != "password"})

    async def authenticate_user(self, username: str, password: str):
        user = await self.collection.find_one({"username": username})
        if not user:
            return False
        if not self.verify_password(password, user["password"]):
            return False
        return user

    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm="HS256")
        return encoded_jwt

    async def login(self, request: LoginRequest) -> LoginResponse:
        user = await self.authenticate_user(request.username, request.password)
        if not user:
            raise ValueError("Invalid credentials")
        access_token = self.create_access_token(data={"sub": user["username"], "role": user["role"]})
        return LoginResponse(access_token=access_token, role=user["role"])

    def decode_token(self, token: str):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            username: str = payload.get("sub")
            role: str = payload.get("role")
            if username is None or role is None:
                return None
            return {"username": username, "role": role}
        except JWTError:
            return None

# Dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    db = get_database()
    auth_service = AuthService(db)
    payload = auth_service.decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await db.users.find_one({"username": payload["username"]})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"username": user["username"], "role": user["role"], "user_id": str(user["_id"])}

async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security_optional)):
    if credentials is None:
        return None
    
    token = credentials.credentials
    db = get_database()
    auth_service = AuthService(db)
    payload = auth_service.decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await db.users.find_one({"username": payload["username"]})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"username": user["username"], "role": user["role"], "user_id": str(user["_id"])}

def require_role(required_role: str):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return current_user
    return role_checker

def require_roles(allowed_roles: list):
    def roles_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return current_user
    return roles_checker