from pydantic import BaseModel,EmailStr
from datetime import datetime
from uuid import UUID
from enum import Enum
from app.models import UserStatus

class ShowUserDeatils(BaseModel):
    id: UUID
    name: str
    phone_num: int
    email: str
    role: str
    status: UserStatus
    is_active: bool
    is_verified: bool
    created_at: datetime
    created_by: UUID | None = None
    updated_at: datetime | None = None
    updated_by: UUID | None = None
    
class UserProfileUpdate(BaseModel):
    name: str | None = None
    phone_num: int | None = None
    email: EmailStr | None = None