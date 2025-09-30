from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text,BigInteger,ForeignKey
from app.models.models import BaseModel
from sqlalchemy.orm import relationship
import enum
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.sql import func
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID

class UserRole(str, enum.Enum):
    superadmin = "superadmin"
    admin = "admin"
    user = "user"

user_role_enum = ENUM(UserRole, name="userrole", create_type=True, validate_strings=True)

class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"

class RegisterUser(BaseModel):
    __tablename__ = "users"
    
    name = Column(String(200), nullable= False)
    phone_num = Column(BigInteger,nullable= False,unique=True)
    email = Column(String(200), nullable= False,unique=True)
    password = Column(String(200),nullable=False)
    
    # User role and status
    role = Column(user_role_enum,nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Authentication and Security
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, default=func.now(), nullable=False)
        
    @property
    def is_locked(self) -> bool:
        if not self.locked_until:
            return False
        return datetime.utcnow() < self.locked_until