from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: str | None = None
    address: str | None = None

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    phone: Optional[str]
    address: Optional[str]
    role: str
    status: str

    model_config = {
        "from_attributes": True
    }

class UserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    address: str | None = None