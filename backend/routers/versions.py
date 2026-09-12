"""
CONTINUO — Versioning & Context Diff Router
Endpoints for inspecting project memory evolution and computing granular diffs.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Project, ProjectVersion, ContextPackage
from backend.schemas import ProjectVersionResponse, ContextDiffResponse
from backend.services.auth import get_current_user
from backend.services.version_diff import VersionDiffEngine

router = APIRouter(prefix="/versions", tags=["Versioning & Diff"])

@router.get("/projects/{project_id}", response_model=List[ProjectVersionResponse])
def get_project_versions(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List historical context versions for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this project.")

    versions = (
        db.query(ProjectVersion)
        .filter(ProjectVersion.project_id == project_id)
        .order_by(ProjectVersion.created_at.desc())
        .all()
    )
    return versions

@router.get("/projects/{project_id}/diff", response_model=ContextDiffResponse)
def compute_version_diff(
    project_id: str,
    from_version: str = Query(..., description="Starting version (e.g. v1.0)"),
    to_version: str = Query(..., description="Target version (e.g. v1.1)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compute granular additions, modifications, and removals between two context versions."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this project.")

    pkg_old = (
        db.query(ContextPackage)
        .filter(ContextPackage.project_id == project_id, ContextPackage.version == from_version)
        .first()
    )
    pkg_new = (
        db.query(ContextPackage)
        .filter(ContextPackage.project_id == project_id, ContextPackage.version == to_version)
        .first()
    )

    if not pkg_old:
        raise HTTPException(status_code=404, detail=f"Base version '{from_version}' not found.")
    if not pkg_new:
        raise HTTPException(status_code=404, detail=f"Target version '{to_version}' not found.")

    def to_dict(pkg: ContextPackage) -> Dict[str, Any]:
        return {
            "objective": pkg.objective,
            "current_state": pkg.current_state,
            "requirements": pkg.get_list("requirements"),
            "constraints": pkg.get_list("constraints"),
            "instructions": pkg.get_list("instructions"),
            "decisions": pkg.get_list("decisions"),
            "completed_work": pkg.get_list("completed_work"),
            "pending_work": pkg.get_list("pending_work"),
            "open_problems": pkg.get_list("open_problems"),
            "failed_attempts": pkg.get_list("failed_attempts"),
            "files_context": pkg.get_list("files_context"),
            "design_decisions": pkg.get_list("design_decisions"),
            "dependencies": pkg.get_list("dependencies"),
            "next_steps": pkg.get_list("next_steps"),
        }

    diff_result = VersionDiffEngine.compute_diff(
        to_dict(pkg_old),
        to_dict(pkg_new),
        from_version,
        to_version,
        project_id
    )

    return diff_result
