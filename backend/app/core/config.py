from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Evolve Hair Studio API"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"
    
    DATABASE_URL: Optional[str] = None
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None
    SUPABASE_JWKS_URL: Optional[str] = None
    SUPABASE_SECRET_KEY: Optional[str] = None
    RESEND_API_KEY: Optional[str] = None
    RESEND_FROM_EMAIL: str = "EVOLVE <onboarding@resend.dev>"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
