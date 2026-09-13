"""
CONTINUO — Backend Configuration
Environment and settings management via pydantic.
"""

import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "Continuo Context Platform"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Secret Key for JWT Token Generation
    SECRET_KEY: str = os.getenv("SECRET_KEY", "continuo_dev_secret_key_9f8e7d6c5b4a3b2a1")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    # Database Configuration (SQLite default with zero setup, PostgreSQL/Supabase ready)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./continuo.db")
    
    # CORS Origins (configurable via environment variable)
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "").split(",")
        if origin.strip()
    ] or [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

settings = Settings()
