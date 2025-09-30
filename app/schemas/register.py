from pydantic import BaseModel,EmailStr
from uuid import UUID
from datetime import datetime
from app.models import UserRole

class Base(BaseModel):
    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_active: bool | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    
    class Config:
        from_attributes = True
    
class UserRegister(BaseModel):
    name: str
    phone_num: int
    email: EmailStr
    password: str

class UserRegisterResponse(Base):
    name: str
    phone_num: int
    email: str
    role: UserRole
    
    class Config:
        from_attributes = True
    