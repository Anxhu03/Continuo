"""
CONTINUO — Context Tasks Router
REST API endpoints for project-scoped, user-isolated ContextTask entities.
Enforces task lifecycle transitions and automated completed_at timestamp tracking.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Project, ContextTask, Conversation, utc_now
from backend.schemas import ContextTaskCreate, ContextTaskUpdate, ContextTaskResponse
from backend.services.auth import get_current_user

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["Context Tasks"])


def _verify_project_ownership(project_id: str, db: Session, current_user: User) -> Project:
    """Verify that the target project exists and belongs to the authenticated user."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You do not own this project.")
    return project


def _validate_source_session(source_session_id: Optional[str], project_id: str, db: Session) -> None:
    """Validate that the referenced source session exists and belongs to the same project."""
    if not source_session_id:
        return
    conv = db.query(Conversation).filter(Conversation.id == source_session_id).first()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid source_session_id: Conversation session does not exist."
        )
    if conv.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid source_session_id: Conversation session does not belong to this project."
        )


@router.post("", response_model=ContextTaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    project_id: str,
    task_in: ContextTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new context task for the specified project."""
    project = _verify_project_ownership(project_id, db, current_user)
    _validate_source_session(task_in.source_session_id, project.id, db)

    task_status = task_in.status or "todo"
    completed_at = None
    if task_status == "completed":
        completed_at = task_in.completed_at or utc_now()

    task = ContextTask(
        project_id=project.id,
        user_id=current_user.id,
        title=task_in.title,
        description=task_in.description,
        status=task_status,
        priority=task_in.priority or "normal",
        source_session_id=task_in.source_session_id,
        completed_at=completed_at,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=List[ContextTaskResponse])
def list_tasks(
    project_id: str,
    status: Optional[str] = Query(None, description="Filter by task status"),
    priority: Optional[str] = Query(None, description="Filter by task priority"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all context tasks for the specified project with optional filtering."""
    project = _verify_project_ownership(project_id, db, current_user)

    query = db.query(ContextTask).filter(ContextTask.project_id == project.id)
    if status is not None:
        query = query.filter(ContextTask.status == status)
    if priority is not None:
        query = query.filter(ContextTask.priority == priority)

    return query.order_by(ContextTask.updated_at.desc()).all()


@router.get("/{task_id}", response_model=ContextTaskResponse)
def get_task(
    project_id: str,
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a single context task by ID within the specified project."""
    project = _verify_project_ownership(project_id, db, current_user)

    task = db.query(ContextTask).filter(
        ContextTask.id == task_id,
        ContextTask.project_id == project.id,
    ).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    return task


@router.patch("/{task_id}", response_model=ContextTaskResponse)
def update_task(
    project_id: str,
    task_id: str,
    task_in: ContextTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update attributes of a context task.
    Automatically manages completed_at timestamp on lifecycle transitions.
    """
    project = _verify_project_ownership(project_id, db, current_user)

    task = db.query(ContextTask).filter(
        ContextTask.id == task_id,
        ContextTask.project_id == project.id,
    ).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    if task_in.source_session_id is not None:
        _validate_source_session(task_in.source_session_id, project.id, db)
        task.source_session_id = task_in.source_session_id

    if task_in.title is not None:
        task.title = task_in.title
    if task_in.description is not None:
        task.description = task_in.description
    if task_in.priority is not None:
        task.priority = task_in.priority

    # Lifecycle state transition management
    if task_in.status is not None:
        new_status = task_in.status
        task.status = new_status
        if new_status == "completed":
            if not task.completed_at:
                task.completed_at = task_in.completed_at or utc_now()
        elif new_status in {"todo", "in_progress", "blocked", "cancelled"}:
            task.completed_at = None
    elif task_in.completed_at is not None and task.status == "completed":
        task.completed_at = task_in.completed_at

    task.updated_at = utc_now()
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    project_id: str,
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a context task from the project."""
    project = _verify_project_ownership(project_id, db, current_user)

    task = db.query(ContextTask).filter(
        ContextTask.id == task_id,
        ContextTask.project_id == project.id,
    ).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    db.delete(task)
    db.commit()
    return None
