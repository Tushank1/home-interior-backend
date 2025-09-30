from pydantic import BaseModel,EmailStr,Field
from app.schemas.register import UserRegisterResponse

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    
class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'
    expires_in: int
    user: UserRegisterResponse
    
class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(...,min_length=1)
    
class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    
class ResetPasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str
    
class EmailRequest(BaseModel):
    email: EmailStr
    
class ForgetResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str
    
class LogoutRequest(BaseModel):
    access_token: str
    refresh_token: str