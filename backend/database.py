"""
CONTINUO — Database Setup & Session Management
SQLAlchemy engine with SQLite and PostgreSQL support.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import settings

# Configure engine options based on dialect
db_url = settings.get_normalized_database_url()
is_sqlite = db_url.startswith("sqlite")

engine_kwargs = {
    "echo": False,
    "future": True,
}

if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
    engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(db_url, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for obtaining database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

import logging
from pathlib import Path

logger = logging.getLogger("continuo.database")

def run_migrations():
    """Apply pending Alembic migrations programmatically."""
    try:
        from alembic.config import Config
        from alembic import command

        alembic_cfg_path = Path(__file__).resolve().parent.parent / "alembic.ini"
        if alembic_cfg_path.exists():
            alembic_cfg = Config(str(alembic_cfg_path))
            alembic_cfg.set_main_option("sqlalchemy.url", settings.get_normalized_database_url())
            command.upgrade(alembic_cfg, "head")
            logger.info("Alembic migrations verified/applied successfully.")
        else:
            logger.warning(f"alembic.ini not found at {alembic_cfg_path}; skipping programmatic migration.")
    except Exception as e:
        logger.error(f"Error applying Alembic migrations: {e}")
        raise

def init_db():
    """Initialize database schema safely based on environment.
    
    In production: Schema management is delegated to Alembic migrations to prevent
    race conditions (e.g. unique constraint collisions on pg_type_typname_nsp_index)
    across concurrent Uvicorn workers.
    
    In development/testing: Creates tables via Base.metadata.create_all() if not already present.
    """
    if settings.ENVIRONMENT == "production":
        logger.info(
            "Production environment detected: schema management is delegated to "
            "Alembic migrations. Skipping Base.metadata.create_all() to prevent race conditions."
        )
        return

    # Development / Testing fallback
    import backend.models  # noqa
    Base.metadata.create_all(bind=engine)
