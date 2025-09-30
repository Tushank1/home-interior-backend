import logging
from app.core.security import security_manager
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import UserProfileUpdate,UserRegister
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.models import RegisterUser
from app.core.exceptions import ConflictError
from app.services.auth_services import auth_service
from uuid import UUID
from fastapi import HTTPException,status
from pydantic import EmailStr
from datetime import datetime,timezone

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self):
        self.security = security_manager
        self.auth = auth_service
        
    async def create_user(self,db: AsyncSession, data: UserRegister):
        try:
            # Check if email is already exists
            user = await self.auth._get_user_by_email(db,str(data.email))
            logger.debug(f"User fetched by email: {user}")
            if user:
                raise ConflictError("Email already registered")
            
            # Hash password
            hashed_password = self.security.get_hashed_password(data.password)
            
            # Create User
            db_user = RegisterUser(
                name=data.name,
                email=str(data.email),
                password=hashed_password,
                phone_num=data.phone_num,
                role='admin'
            )
            
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
            
            logger.info(f"User created successfully: {db_user.email}")
            
            return db_user
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"IntegrityError details: {e}")
            raise ConflictError(f"DB IntegrityError: {str(e)}")
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating user: {str(e)}")
            raise
        
    async def get_all(self,db: AsyncSession,skip: int = 0,limit: int = 100):
        try:
            stmt = await db.execute(select(RegisterUser).offset(skip).limit(limit))
            user_response = stmt.scalars().all()
            
            if not user_response:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="There is no user available.")

            return user_response
        except Exception as e:
            logger.error(f"Error :- {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Error while fetching all users.")
        
    async def get_by_id(self,db: AsyncSession,user_id: UUID):
        try:
            stmt = await db.execute(select(RegisterUser).where(RegisterUser.id == user_id))
            user_response = stmt.scalar_one_or_none()
            
            if not user_response:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="There is no user available.")

            return user_response
        except Exception as e:
            logger.error(f"Error :- {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Error while fetching all users.")
        
    async def update_profile(self,db: AsyncSession, data: UserProfileUpdate,user_id: UUID):
        try:
            stmt = await db.execute(select(RegisterUser).where(RegisterUser.id == user_id))
            result = stmt.scalar_one_or_none()
            
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found.")

            update_data = data.model_dump(exclude_unset=True)
            
            update_data = {k: v for k, v in update_data.items() if v not in ['string', 'user@example.com']}

            for key, value in update_data.items():
                if isinstance(value,EmailStr):
                    value = str(value)
                setattr(result, key, value)

                
            result.updated_by = user_id
            result.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            
            db.add(result)
            await db.commit()
            await db.refresh(result)
            
            return result
            
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Error while updating profile details.")
    
user_service = UserService()