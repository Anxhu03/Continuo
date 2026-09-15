"""
CONTINUO — Database Initialization and Production Safety Tests
"""

import importlib.util
from pathlib import Path
from unittest.mock import patch
from backend.config import settings
from backend.database import init_db

# Load migration module directly by file path to avoid package shadowing
migration_path = Path(__file__).resolve().parent.parent / "alembic" / "versions" / "0001_initial_schema.py"
spec = importlib.util.spec_from_file_location("initial_schema", migration_path)
migration_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration_module)

relation_or_type_exists = migration_module.relation_or_type_exists
index_exists = migration_module.index_exists

def test_health_and_root_endpoints(client):
    """Verify GET and HEAD on / and /health return 200 OK."""
    # Root GET
    root_get = client.get("/")
    assert root_get.status_code == 200
    data = root_get.json()
    assert data["status"] == "operational"

    # Root HEAD
    root_head = client.head("/")
    assert root_head.status_code == 200

    # Health GET
    health_get = client.get("/health")
    assert health_get.status_code == 200
    assert health_get.json()["status"] == "operational"

    # Health HEAD
    health_head = client.head("/health")
    assert health_head.status_code == 200

    # API v1 Health
    v1_health = client.get("/api/v1/health")
    assert v1_health.status_code == 200

def test_init_db_production_skips_create_all():
    """Verify init_db() in production does NOT call Base.metadata.create_all."""
    with patch.object(settings, "ENVIRONMENT", "production"):
        with patch("backend.database.Base.metadata.create_all") as mock_create_all:
            init_db()
            mock_create_all.assert_not_called()

def test_init_db_development_calls_create_all():
    """Verify init_db() in development calls Base.metadata.create_all."""
    with patch.object(settings, "ENVIRONMENT", "development"):
        with patch("backend.database.Base.metadata.create_all") as mock_create_all:
            init_db()
            mock_create_all.assert_called_once()

def test_relation_or_type_exists_helper(db_session):
    """Verify relation_or_type_exists detects created tables."""
    bind = db_session.get_bind()
    assert relation_or_type_exists(bind, "users") is True
    assert relation_or_type_exists(bind, "projects") is True
    assert relation_or_type_exists(bind, "non_existent_table_xyz") is False

def test_index_exists_helper(db_session):
    """Verify index_exists detects existing indexes."""
    bind = db_session.get_bind()
    assert index_exists(bind, "users", "ix_users_email") is True
    assert index_exists(bind, "users", "non_existent_index_xyz") is False
