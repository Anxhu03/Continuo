"""
CONTINUO — Admin & Developer Diagnostics Router
Protected diagnostics and platform metrics strictly enforced for 'admin' and 'developer' roles.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Project, ContextPackage
from backend.schemas import DiagnosticsResponse
from backend.services.auth import require_role
from backend.config import settings

router = APIRouter(prefix="/admin", tags=["Admin & Diagnostics"])

@router.get("/diagnostics", response_model=DiagnosticsResponse)
def get_diagnostics(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role(["admin", "developer"]))
):
    """
    Retrieve system health, database metrics, and gateway diagnostics.
    Strictly enforced server-side for admin and developer roles (returns 403 for standard users).
    """
    total_users = db.query(User).count()
    total_projects = db.query(Project).count()
    total_pkgs = db.query(ContextPackage).count()

    return DiagnosticsResponse(
        status="operational",
        role=admin_user.role,
        gateway_port=8008,
        database="SQLite / Supabase RLS Ready",
        active_users=total_users,
        active_projects=total_projects,
        total_context_packages=total_pkgs,
        version=settings.VERSION,
        features={
            "role_based_access": True,
            "jwt_stateless_verification": True,
            "user_level_project_isolation": True,
            "manifest_v3_relay": True,
            "supported_adapters": ["ChatGPT", "Claude", "Gemini", "Cursor"],
            "quality_weights": {
                "completeness": 0.30,
                "consistency": 0.20,
                "relevance": 0.25,
                "actionability": 0.25
            }
        }
    )
