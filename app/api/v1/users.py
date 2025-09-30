from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.db_connection import get_db
import logging
from app.schemas import ShowUserDeatils,UserProfileUpdate
from app.services import user_service
from app.models import RegisterUser
from app.core.dependencies import get_current_active_user,get_optional_current_user
from typing import List,Optional
from uuid import UUID

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
router = APIRouter(prefix="/user",tags=['Users'])

@router.get("/",response_model=List[ShowUserDeatils],status_code=status.HTTP_200_OK)
async def get_all_users(skip: int = 0,limit: int = 100,db: AsyncSession = Depends(get_db),current_user: Optional[RegisterUser] = Depends(get_optional_current_user)):
    users = await user_service.get_all(db,skip,limit)         
    return [ShowUserDeatils.model_validate(user,from_attributes=True) for user in users]

@router.get("/{id}",response_model=ShowUserDeatils,status_code=status.HTTP_200_OK)
async def get_user_by_id(id: UUID,db: AsyncSession = Depends(get_db),current_user: dict = Depends(get_current_active_user)):
    users = await user_service.get_by_id(db,id)
    return ShowUserDeatils.model_validate(users,from_attributes=True)

@router.patch("/update",response_model=ShowUserDeatils,status_code=status.HTTP_200_OK)
async def update_profile_details(request: UserProfileUpdate,db: AsyncSession = Depends(get_db),current_user: dict = Depends(get_current_active_user)):
    user_data = {k: v for k, v in vars(current_user).items() if not k.startswith('_')}
    user_id = user_data['id']
    return await user_service.update_profile(db,request,user_id)