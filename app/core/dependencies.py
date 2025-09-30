from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import RegisterUser
from app.core.security import security_manager
from app.core.exceptions import AuthenticationError
from app.config.db_connection import get_db
from app.services.auth_services import auth_service
from typing import List,Optional

security = HTTPBearer(auto_error=False)

async def get_optional_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),db: AsyncSession = Depends(get_db)):
    """Get user if token is provided; otherwise return None."""
    if credentials is None:
        return None  # No token provided

    try:
        token_data = await security_manager.verify_access_token(credentials.credentials,db,'access')
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
            
        user = await auth_service._get_user_by_id(db, token_data['id'])
        
        if user and user.is_active:
            return user
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not active or not found",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security),db: AsyncSession = Depends(get_db)):
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Please provide token")
    token_data = await security_manager.verify_access_token(credentials.credentials,db,'access')
    if not token_data:
        raise credentials_exception
    
    user_id = token_data['id']
    if not user_id:
        raise credentials_exception
    
    # Get user from db
    user = await auth_service._get_user_by_id(db,user_id)
    
    if not user:
        raise credentials_exception
    
    if not user.is_active:
        raise AuthenticationError("User account is deactivated")
    
    return user

async def get_current_active_user(current_user: RegisterUser = Depends(get_current_user)):
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

def require_role(required_role: List[str]):
    def role_checker(user: dict = Depends(get_current_active_user)):
        if user['role'] not in required_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Permission denied")
        return user
    return role_checker

