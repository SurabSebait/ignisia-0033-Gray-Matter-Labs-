from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    username: str
    role: str  # user/admin/support

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str