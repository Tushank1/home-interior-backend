from pydantic_settings import BaseSettings,SettingsConfigDict
from typing import List,Optional
from pydantic import Field
from pathlib import Path

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    ngrok_auth_token: str | None = None
    
    # App Settings
    app_name: str = Field(default="Smart Home Interior API")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    allowed_hosts: List[str] = Field(default=["localhost", "127.0.0.1"])

    # Database Settings
    database_url_async: str = Field(..., env="DATABASE_URL_ASYNC")
    database_url_sync: str = Field(..., env="DATABASE_URL_SYNC")

    # JWT Settings
    jwt_algorithm: str = Field(default="PS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    reset_token_expire_minutes: int = Field(default=1440,env="RESET_TOKEN_EXPIRE_MINUTES")
    jwt_private_key_path: str = Field(..., env="JWT_PRIVATE_KEY_PATH")
    jwt_public_key_path: str = Field(..., env="JWT_PUBLIC_KEY_PATH")

    # Email Settings
    smtp_server: Optional[str] = Field(default=None, env="SMTP_SERVER")
    smtp_from_address: str = Field(...,env="SMTP_FROM_ADDRESS")
    smtp_port: Optional[int] = Field(default=587, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    web_url: str = Field(...,env="WEB_URL")

    # Security Settings
    bcrypt_rounds: int = Field(default=12, env="BCRYPT_ROUNDS")
    max_login_attempts: int = Field(default=5, env="MAX_LOGIN_ATTEMPTS")
    lockout_duration_minutes: int = Field(default=30, env="LOCKOUT_DURATION_MINUTES")
    
    # File Upload
    upload_dir: str = Field(default="/app/uploads", env="UPLOAD_DIR")
    max_file_size: int = Field(default=100 * 1024 * 1024, env="MAX_FILE_SIZE")
    
    # CORS
    cors_origins: List[str] = Field(default=["http://localhost:3000", "http://localhost:8080"], env="CORS_ORIGINS")

    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug_env: bool = Field(default=False, env="DEBUG")
    
    @property
    def jwt_private_key(self) -> str:
        path = Path(self.jwt_private_key_path)
        if not path.exists():
            raise FileNotFoundError(f"Private key not found: {path}")
        return path.read_text().strip()

    @property
    def jwt_public_key(self) -> str:
        path = Path(self.jwt_public_key_path)
        if not path.exists():
            raise FileNotFoundError(f"Public key not found: {path}")
        return path.read_text().strip()
    
print(f"Loading environment varibales ...")
settings = Settings()   