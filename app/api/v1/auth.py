from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.db_connection import get_db
import logging
from app.schemas import LoginRequest, LoginResponse,RefreshTokenRequest,RefreshTokenResponse,ResetPasswordRequest,EmailRequest,ForgetResetPasswordRequest,UserRegisterResponse,UserRegister,LogoutRequest
from app.core.exceptions import AuthenticationError, ValidationError, ConflictError
from app.services import auth_service,user_service
from app.core.dependencies import get_current_user,get_current_active_user

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
router = APIRouter(prefix="/auth",tags=['Authentication'])

@router.post("/register",response_model=UserRegisterResponse,status_code=status.HTTP_200_OK)
async def register(user_data: UserRegister,db: AsyncSession = Depends(get_db)):
    try:
        # current_user_data = {k: v for k, v in vars(current_user).items() if not k.startswith('_')}
        # user_role = current_user_data['role'].value
        
        user = await user_service.create_user(db,user_data)
        return UserRegisterResponse.model_validate(user)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed")
    
@router.post("/login",response_model=LoginResponse,status_code=status.HTTP_200_OK)
async def login(login_data: LoginRequest,db: AsyncSession = Depends(get_db)):
    """Login user."""
    return await auth_service.login(db,login_data)
    
@router.post("/logout",status_code=status.HTTP_200_OK)
async def logout(request: LogoutRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.logout_access(db,request)
    
@router.post("/refresh",response_model=RefreshTokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(refresh_data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token."""
    try:
        return await auth_service.refresh_token(db,refresh_data)
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error(f"Error during token refresh: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Token refresh failed")
    
@router.post("/update_password",status_code=status.HTTP_200_OK)
async def update_password(request: ResetPasswordRequest,db: AsyncSession = Depends(get_db),current_user: dict = Depends(get_current_user)):
    """Update password using token."""
    try:
        user_data = {k: v for k, v in vars(current_user).items() if not k.startswith('_')}
        email = user_data['email']
        
        await auth_service.reset_password(db,request,email)
        return {"message": "Password reset successful"}
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
@router.post("/forgot_password",status_code=status.HTTP_200_OK)
async def forgot_password(emailRequest: EmailRequest,db: AsyncSession = Depends(get_db)):
    try:        
        return await auth_service.forget_reset_password_mail(db,str(emailRequest.email))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
@router.post("/new_password",status_code=status.HTTP_200_OK)
async def forget_reset_password(data: ForgetResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await auth_service.forget_reset_password(db,data)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))