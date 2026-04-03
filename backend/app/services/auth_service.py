from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.user import UserCreate, User, LoginRequest, LoginResponse
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from app.config.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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