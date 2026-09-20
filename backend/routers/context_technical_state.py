"""
CONTINUO — Context Technical State Router
REST API endpoints for project-scoped, user-isolated ContextTechnicalState entities.
Enforces unique key-value constraints and handles conflict scenarios cleanly.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Project, ContextTechnicalState, Conversation, utc_now
from backend.schemas import (
    ContextTechnicalStateCreate,
    ContextTechnicalStateUpdate,
    ContextTechnicalStateResponse,
)
from backend.services.auth import get_current_user

router = APIRouter(prefix="/projects/{project_id}/technical-state", tags=["Context Technical State"])


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


@router.post("", response_model=ContextTechnicalStateResponse, status_code=status.HTTP_201_CREATED)
def create_technical_state(
    project_id: str,
    state_in: ContextTechnicalStateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new technical state key-value record for the specified project.
    Enforces uniqueness of (project_id, category, key) with HTTP 409 Conflict.
    """
    project = _verify_project_ownership(project_id, db, current_user)
    _validate_source_session(state_in.source_session_id, project.id, db)

    # Proactive check against unique constraint
    existing = db.query(ContextTechnicalState).filter(
        ContextTechnicalState.project_id == project.id,
        ContextTechnicalState.category == state_in.category,
        ContextTechnicalState.key == state_in.key,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Technical state for category '{state_in.category}' and key '{state_in.key}' already exists in this project."
        )

    state_obj = ContextTechnicalState(
        project_id=project.id,
        user_id=current_user.id,
        category=state_in.category,
        key=state_in.key,
        value=state_in.value,
        source_session_id=state_in.source_session_id,
    )

    try:
        db.add(state_obj)
        db.commit()
        db.refresh(state_obj)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Technical state for category '{state_in.category}' and key '{state_in.key}' already exists in this project."
        )

    return state_obj


@router.get("", response_model=List[ContextTechnicalStateResponse])
def list_technical_state(
    project_id: str,
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all technical state records for the project with optional category filtering."""
    project = _verify_project_ownership(project_id, db, current_user)

    query = db.query(ContextTechnicalState).filter(ContextTechnicalState.project_id == project.id)
    if category is not None:
        query = query.filter(ContextTechnicalState.category == category)

    return query.order_by(ContextTechnicalState.updated_at.desc()).all()


@router.get("/{state_id}", response_model=ContextTechnicalStateResponse)
def get_technical_state(
    project_id: str,
    state_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a single technical state record by ID within the project."""
    project = _verify_project_ownership(project_id, db, current_user)

    state_obj = db.query(ContextTechnicalState).filter(
        ContextTechnicalState.id == state_id,
        ContextTechnicalState.project_id == project.id,
    ).first()
    if not state_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Technical state not found.")
    return state_obj


@router.patch("/{state_id}", response_model=ContextTechnicalStateResponse)
def update_technical_state(
    project_id: str,
    state_id: str,
    state_in: ContextTechnicalStateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update attributes of a technical state record, handling potential key conflicts cleanly."""
    project = _verify_project_ownership(project_id, db, current_user)

    state_obj = db.query(ContextTechnicalState).filter(
        ContextTechnicalState.id == state_id,
        ContextTechnicalState.project_id == project.id,
    ).first()
    if not state_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Technical state not found.")

    if state_in.source_session_id is not None:
        _validate_source_session(state_in.source_session_id, project.id, db)
        state_obj.source_session_id = state_in.source_session_id

    new_cat = state_in.category if state_in.category is not None else state_obj.category
    new_key = state_in.key if state_in.key is not None else state_obj.key

    # Check for conflict if category or key is changing
    if new_cat != state_obj.category or new_key != state_obj.key:
        conflict = db.query(ContextTechnicalState).filter(
            ContextTechnicalState.project_id == project.id,
            ContextTechnicalState.category == new_cat,
            ContextTechnicalState.key == new_key,
            ContextTechnicalState.id != state_id,
        ).first()
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Technical state for category '{new_cat}' and key '{new_key}' already exists in this project."
            )

    if state_in.category is not None:
        state_obj.category = state_in.category
    if state_in.key is not None:
        state_obj.key = state_in.key
    if state_in.value is not None:
        state_obj.value = state_in.value

    state_obj.updated_at = utc_now()

    try:
        db.commit()
        db.refresh(state_obj)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Technical state for category '{new_cat}' and key '{new_key}' already exists in this project."
        )

    return state_obj


@router.delete("/{state_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_technical_state(
    project_id: str,
    state_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a technical state record from the project."""
    project = _verify_project_ownership(project_id, db, current_user)

    state_obj = db.query(ContextTechnicalState).filter(
        ContextTechnicalState.id == state_id,
        ContextTechnicalState.project_id == project.id,
    ).first()
    if not state_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Technical state not found.")

    db.delete(state_obj)
    db.commit()
    return None
