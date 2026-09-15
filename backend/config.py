"""
CONTINUO — Backend Configuration
Environment and settings management via pydantic.
"""

import os
from pydantic import BaseModel, Field, model_validator

class Settings(BaseModel):
    PROJECT_NAME: str = "Continuo Context Platform"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://continuo-one.vercel.app")
    
    # Secret Key for JWT Token Generation
    SECRET_KEY: str = os.getenv("SECRET_KEY", "continuo_dev_secret_key_9f8e7d6c5b4a3b2a1")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    # Database Configuration (SQLite default for local dev, PostgreSQL/Supabase ready)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./continuo.db")
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    
    # CORS Origins (configurable via environment variable or auto-detected based on ENVIRONMENT)
    CORS_ORIGINS: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def compute_cors_origins(self) -> "Settings":
        if not self.CORS_ORIGINS:
            env_cors = os.getenv("CORS_ORIGINS", "")
            if env_cors.strip():
                origins = [o.strip() for o in env_cors.split(",") if o.strip()]
                if "https://continuo-one.vercel.app" not in origins:
                    origins.append("https://continuo-one.vercel.app")
                self.CORS_ORIGINS = origins
            elif self.ENVIRONMENT == "production":
                self.CORS_ORIGINS = [
                    "https://continuo-one.vercel.app",
                    "https://continuo-api.onrender.com",
                    "https://continuo.run.place",
                    "https://api.continuo.run.place"
                ]
            else:
                self.CORS_ORIGINS = [
                    "https://continuo-one.vercel.app",
                    "http://localhost:8008",
                    "http://127.0.0.1:8008",
                    "http://localhost:8000",
                    "http://127.0.0.1:8000",
                    "http://localhost:3000",
                    "http://127.0.0.1:3000",
                    "http://localhost:5173",
                    "http://127.0.0.1:5173",
                ]
        return self

    def get_normalized_database_url(self) -> str:
        """Ensure postgres:// is converted to postgresql:// for SQLAlchemy driver compatibility."""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql://", 1)
        return url

settings = Settings()

