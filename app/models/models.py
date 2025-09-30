"""
Database Models for Master Data Management
Optimized for Enterprise-Level Performance and Scalability
"""

from sqlalchemy import Column, Boolean, DateTime, ForeignKey,String
from app.config.db_connection import Base
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

# Base Model for common fields
class BaseModel(Base):
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True),primary_key=True,index=True,default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean,default=True,index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"),nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"),nullable=True)
    

class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"
    
    id = Column(UUID(as_uuid=True),primary_key=True,index=True,default=uuid.uuid4)
    jti = Column(String, unique=True, index=True)
    expires_at = Column(DateTime)