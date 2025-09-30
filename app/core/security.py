from fastapi import HTTPException,status
from datetime import datetime,timedelta
import jwt,uuid
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from passlib.context import CryptContext
from app.config.settings import settings
from app.models import BlacklistedToken
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class SecurityManager:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        self.refresh_token_expiry_day = settings.refresh_token_expire_days
        self.reset_token_expire_minutes = settings.reset_token_expire_minutes

        # For PS256 use RSA keys
        self.private_key = settings.jwt_private_key
        self.public_key = settings.jwt_public_key
        
    def verify_password(self,plain_password: str,hashed_password: str):
        "Verfiy a plain password against a hashed password"
        return self.pwd_context.verify(plain_password,hashed_password)
    
    def get_hashed_password(self,password: str):
        """"Hash a password"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self,data: dict,expire_delta: timedelta | None = None):
        """Create an access token"""
        data['jti'] = str(uuid.uuid4())
        to_encode = data.copy()
        if expire_delta:
            expire = datetime.utcnow() + expire_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire,'type':'access'})
        encoded_jwt = jwt.encode(to_encode, self.private_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self,data: dict,expire_delta: timedelta | None = None):
        """Create an Refresh token"""
        data['jti'] = str(uuid.uuid4())
        to_encode = data.copy()
        if expire_delta:
            expire = datetime.utcnow() + expire_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expiry_day)
        to_encode.update({"exp": expire,'type':'refresh'})
        encoded_jwt = jwt.encode(to_encode,self.private_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_forgot_password_reset_token(self,data: dict,expire_delta: timedelta | None = None):
        """Create forgot password reset token"""
        to_encode = data.copy()
        if expire_delta:
            expire = datetime.utcnow() + expire_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.reset_token_expire_minutes)
        to_encode.update({"exp": expire,"type": 'reset'})
        return jwt.encode(to_encode,self.private_key,algorithm=self.algorithm)
    
    async def verify_access_token(self,token: str,db: AsyncSession, token_type: str = 'access'):
        """Verify and decode a token"""
        try:
            payload = jwt.decode(token,self.public_key,algorithms=[self.algorithm])
            jti = payload.get("jti")
            
            # Check Blacklist
            if await self.is_token_blacklisted(jti,db):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Token is blacklisted")
            
            if payload.get("type") != token_type:
                return None
            
            return payload
        except ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        except InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
    async def verify_refresh_token(self,token: str ,db: AsyncSession,token_type: str = 'refresh'):
        """Verify and decode a token"""
        try:
            payload = jwt.decode(token,self.public_key,algorithms=[self.algorithm])
            jti = payload.get("jti")
            
            # Check Blacklist
            if await self.is_token_blacklisted(jti,db):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Token is blacklisted")
                
            if payload.get("type") != token_type:
                return None
            return payload
        except ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        except InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
    def verify_forget_reset_password_token(self,token: str,token_type: str):
        """Verfiy forget Reset password token"""
        try:
            payload = jwt.decode(token,self.public_key,algorithms=[self.algorithm])
            if payload.get("token_type") != token_type:
                return None
            return payload
        except ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        except InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
    async def is_token_blacklisted(self,jti: str, db: AsyncSession) -> bool:
        result = await db.execute(select(BlacklistedToken).where(BlacklistedToken.jti == jti))
        return result.scalar_one_or_none() is not None
security_manager = SecurityManager()