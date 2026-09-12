"""
CONTINUO — Projects Router
Endpoints for managing project lifecycle, metadata, and persistence.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Project, ContextPackage, ProjectVersion
from backend.schemas import ProjectCreate, ProjectUpdate, ProjectResponse
from backend.services.auth import get_current_user

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("", response_model=List[ProjectResponse])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all projects owned by the authenticated user."""
    projects = (
        db.query(Project)
        .filter(Project.user_id == current_user.id)
        .order_by(Project.updated_at.desc())
        .all()
    )
    return projects

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new project and initialize its root ContextPackage (v1.0)."""
    project = Project(
        user_id=current_user.id,
        name=project_in.name,
        description=project_in.description,
        current_version="v1.0",
        health_score=85.0
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Automatically generate initial ContextPackage v1.0
    objective_text = project_in.initial_objective or f"Develop and deploy {project.name} features."
    pkg = ContextPackage(
        project_id=project.id,
        version="v1.0",
        objective=objective_text,
        current_state="Project initialized. Ready for AI context capture.",
        quality_score=85.0
    )
    pkg.set_list("requirements", ["Establish core application architecture and persistence layer"])
    pkg.set_list("constraints", ["Maintain backward compatibility across all modules"])
    pkg.set_list("decisions", ["Initialized on Continuo Context Continuity Layer"])
    pkg.set_list("next_steps", ["Capture first conversation transcript or import project files"])
    
    db.add(pkg)
    db.commit()
    db.refresh(pkg)

    # Register ProjectVersion v1.0
    ver = ProjectVersion(
        project_id=project.id,
        version_number="v1.0",
        context_package_id=pkg.id,
        changelog="Initial project creation and baseline context establishment."
    )
    db.add(ver)
    db.commit()

    return project

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch details of a single project, verifying user ownership."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this project.")
    return project

@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update project name or description."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this project.")

    if project_in.name is not None:
        project.name = project_in.name
    if project_in.description is not None:
        project.description = project_in.description
    if project_in.current_version is not None:
        project.current_version = project_in.current_version

    db.commit()
    db.refresh(project)
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a project and all associated context packages and versions."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this project.")

    db.delete(project)
    db.commit()
    return None
