import logging,jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import security_manager
from app.config.settings import settings
from sqlalchemy import select
from fastapi import HTTPException,status
from app.core.exceptions import AuthenticationError, ValidationError, NotFoundError
from ..models import RegisterUser,UserStatus,BlacklistedToken
from datetime import datetime,timedelta,timezone
from sqlalchemy.dialects.postgresql import UUID
from ..schemas import RefreshTokenRequest,RefreshTokenResponse,ResetPasswordRequest,ForgetResetPasswordRequest,LoginRequest,LoginResponse,LogoutRequest
from app.core.send_email import send_resend_email
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

logger = logging.getLogger(__name__)

class Authservice:
    def __init__(self):
        self.security = security_manager
        self.max_login_attempts = settings.max_login_attempts
        self.lockout_duration = settings.lockout_duration_minutes
        self.public_key = settings.jwt_public_key
        
    async def authenticate_user(self,db: AsyncSession, email: str,password: str):
        """Authenticate user by email and password."""
        user = await self._get_user_by_email(db,email)
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="There is no user of this email id.")
        
        # Check if account is locked
        if user.is_locked:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,detail="Account is temporarily locked due to too many failed login attempts")
        
        # Verify password
        if not self.security.verify_password(password,user.password):
            await self._handle_failed_login(db,user)
            return None
        
        # Reset failed login attempts on successfull login
        if user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            user.locked_until = None
            
        # Update last login
        user.last_login_at = datetime.utcnow()
        await db.commit()
        
        return user
    
    async def login(self,db: AsyncSession,login_data: LoginRequest):
        """Login user and return tokens."""
        user = await self.authenticate_user(db,login_data.email,login_data.password)
        
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Invalid email or password.")
        
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Account is deactived.")
        
        if user.status == UserStatus.SUSPENDED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Account is suspended.")
        
        # Create token
        access_token_expire = timedelta(minutes=settings.access_token_expire_minutes)
        refresh_token_expire = timedelta(days=settings.refresh_token_expire_days)
        
        token_data = {
            "id": str(user.id),
            "email": user.email,
            "role": user.role
        }
        
        access_token = self.security.create_access_token(data=token_data,expire_delta=access_token_expire)
        refresh_token = self.security.create_refresh_token(data=token_data,expire_delta=refresh_token_expire)
                
        logger.info(f"User logged in successfully: {user.email}")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(access_token_expire.total_seconds()),
            user=user.__dict__
        )
        
    async def logout_access(self,db: AsyncSession,data: LogoutRequest):
        for token in [data.access_token,data.refresh_token]:
            try:
                payload = jwt.decode(token, self.public_key, algorithms=["PS256"])
                jti = payload.get("jti")
                exp_timestamp = payload.get("exp")
                
                if not jti or not exp_timestamp:
                    raise HTTPException(status_code=400, detail="Invalid token payload")

                expires_at = datetime.utcfromtimestamp(exp_timestamp)
                
                # Store jti in blacklist
                blacklisted_token = BlacklistedToken(jti=jti, expires_at=expires_at)
                db.add(blacklisted_token)
                
            except ExpiredSignatureError:
                raise HTTPException(status_code=401, detail="Token expired")
            except InvalidTokenError:
                raise HTTPException(status_code=401, detail="Invalid token") 
        
        await db.commit()
                    
        return {"message": "Successfully logged out"}
        
    async def refresh_token(self,db: AsyncSession,refresh_request: RefreshTokenRequest):
        """Refresh access token using refresh token."""
        token_data = self.security.verify_refresh_token(refresh_request.refresh_token,db,"refresh")
        
        if not token_data:
            raise AuthenticationError("Invalid refresh token")
        
        user_id = token_data.get("id")
        if not user_id:
            raise AuthenticationError("Invalid token payload")
        
        # Get user and verify status
        user = await self._get_user_by_id(db,user_id)
        if not user:
            raise AuthenticationError("User not found in DB")

        if not user.is_active:
            raise AuthenticationError("User is inactive")
        
        # Create new access token
        access_token_expire = timedelta(minutes=settings.access_token_expire_minutes)
        new_token_data = {
            "id": str(user.id),
            "email": user.email,
            "role": user.role.value
        }
                
        access_token = self.security.create_access_token(new_token_data,access_token_expire)
        
        return RefreshTokenResponse(
            access_token= access_token,
            token_type= "bearer",
            expires_in= int(access_token_expire.total_seconds())
        )    
        
    async def reset_password(self,db,request: ResetPasswordRequest,email):
        """Reset password."""
        email = email
        if not email:
            raise ValidationError("Invalid or expired reset token")
        
        user = await self._get_user_by_email(db,email)
        if not user:
            raise NotFoundError("User not found")
        
        if not security_manager.verify_password(request.old_password,user.password):
            raise HTTPException(status_code=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION,detail="Your old password is mismatched.")

        if request.confirm_password != request.new_password and request.new_password == request.old_password:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Give different and don't repeat old password.")

        user.password = security_manager.get_hashed_password(request.new_password)
        user.password_changed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        user.failed_login_attempts = 0
        user.locked_until = None
        
        await db.commit()
        
        logger.info(f"Password reset successfully for: {email}")

        return True
    
    async def forget_reset_password_mail(self,db,email: str):
        user = await self._get_user_by_email(db,email)
        
        if not user:
            raise NotFoundError("User not found")
        
        forget_token_expire_time = timedelta(minutes=settings.reset_token_expire_minutes)
        
        token_data = {
            "email": email,
            "token_type": "reset"
        }
        
        forget_reset_password_token = security_manager.create_forgot_password_reset_token(token_data,forget_token_expire_time)
        
        send_resend_email(email,forget_reset_password_token)
        
        return {"message": "Email send successfully."}
    
    async def forget_reset_password(self,db,data: ForgetResetPasswordRequest):
        """Reset User password using forgot password"""
        token_data = security_manager.verify_forget_reset_password_token(data.token,'reset')
        
        if not token_data:
            raise AuthenticationError("Invalid refresh token")
        
        user_email = token_data.get("email")
        if not user_email:
            raise AuthenticationError("Invalid token payload")
        
        # Get user and verify status
        user = await self._get_user_by_email(db,user_email)
        if not user:
            raise AuthenticationError("User not found in DB")
        
        if data.new_password != data.confirm_password:
            raise 
        
        user.password = self.security.get_hashed_password(data.new_password)
        user.password_changed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        user.failed_login_attempts = 0
        user.locked_until = None
        
        await db.commit()
        
        logger.info(f"Password reset successfully for: {user_email}")

        return True
    
    async def _get_user_by_email(self,db: AsyncSession,email: str):
        """Get user by email."""
        stmt = await db.execute(select(RegisterUser).where(RegisterUser.email == email))
        response = stmt.scalar_one_or_none()
        if not response:
            return None
        return response
    
    async def _get_user_by_id(self,db: AsyncSession,id: UUID):
        """Get user by ID."""
        stmt = select(RegisterUser).where(RegisterUser.id == id)
        result = await db.execute(stmt)
        response = result.scalar_one_or_none()
        
        return response
    
    async def _handle_failed_login(self,db: AsyncSession,user: RegisterUser):
        """"Handle failed login"""
        user.failed_login_attempts += 1
        
        if user.failed_login_attempts >= self.max_login_attempts:
            user.locked_until = datetime.utcnow() + timedelta(minutes=self.lockout_duration)
            logger.warning(f"Account locked due to failed login attempts: {user.email}")
            
        await db.commit()
        
auth_service = Authservice()