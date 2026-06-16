from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional
from app.models.user import UserTier


class UserCreate(BaseModel):
    email:     EmailStr
    password:  str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    id:        UUID
    email:     str
    full_name: Optional[str]
    tier:      UserTier

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type:   str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None