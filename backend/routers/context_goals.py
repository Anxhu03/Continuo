"""
CONTINUO — Context Goals Router
REST API endpoints for project-scoped, user-isolated ContextGoal entities.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Project, ContextGoal, Conversation, utc_now
from backend.schemas import ContextGoalCreate, ContextGoalUpdate, ContextGoalResponse
from backend.services.auth import get_current_user

router = APIRouter(prefix="/projects/{project_id}/goals", tags=["Context Goals"])


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


@router.post("", response_model=ContextGoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    project_id: str,
    goal_in: ContextGoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new context goal for the specified project."""
    project = _verify_project_ownership(project_id, db, current_user)
    _validate_source_session(goal_in.source_session_id, project.id, db)

    goal = ContextGoal(
        project_id=project.id,
        user_id=current_user.id,
        title=goal_in.title,
        description=goal_in.description,
        category=goal_in.category or "goal",
        status=goal_in.status or "active",
        priority=goal_in.priority or "normal",
        source_session_id=goal_in.source_session_id,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.get("", response_model=List[ContextGoalResponse])
def list_goals(
    project_id: str,
    status: Optional[str] = Query(None, description="Filter by goal status"),
    priority: Optional[str] = Query(None, description="Filter by goal priority"),
    category: Optional[str] = Query(None, description="Filter by goal category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all context goals for the specified project with optional filtering."""
    project = _verify_project_ownership(project_id, db, current_user)

    query = db.query(ContextGoal).filter(ContextGoal.project_id == project.id)
    if status is not None:
        query = query.filter(ContextGoal.status == status)
    if priority is not None:
        query = query.filter(ContextGoal.priority == priority)
    if category is not None:
        query = query.filter(ContextGoal.category == category)

    return query.order_by(ContextGoal.updated_at.desc()).all()


@router.get("/{goal_id}", response_model=ContextGoalResponse)
def get_goal(
    project_id: str,
    goal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a single context goal by ID within the specified project."""
    project = _verify_project_ownership(project_id, db, current_user)

    goal = db.query(ContextGoal).filter(
        ContextGoal.id == goal_id,
        ContextGoal.project_id == project.id,
    ).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found.")
    return goal


@router.patch("/{goal_id}", response_model=ContextGoalResponse)
def update_goal(
    project_id: str,
    goal_id: str,
    goal_in: ContextGoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update attributes of a context goal."""
    project = _verify_project_ownership(project_id, db, current_user)

    goal = db.query(ContextGoal).filter(
        ContextGoal.id == goal_id,
        ContextGoal.project_id == project.id,
    ).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found.")

    if goal_in.source_session_id is not None:
        _validate_source_session(goal_in.source_session_id, project.id, db)
        goal.source_session_id = goal_in.source_session_id

    if goal_in.title is not None:
        goal.title = goal_in.title
    if goal_in.description is not None:
        goal.description = goal_in.description
    if goal_in.category is not None:
        goal.category = goal_in.category
    if goal_in.status is not None:
        goal.status = goal_in.status
    if goal_in.priority is not None:
        goal.priority = goal_in.priority

    goal.updated_at = utc_now()
    db.commit()
    db.refresh(goal)
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    project_id: str,
    goal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a context goal from the project."""
    project = _verify_project_ownership(project_id, db, current_user)

    goal = db.query(ContextGoal).filter(
        ContextGoal.id == goal_id,
        ContextGoal.project_id == project.id,
    ).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found.")

    db.delete(goal)
    db.commit()
    return None
