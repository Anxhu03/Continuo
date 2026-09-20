"""
CONTINUO — Context Decisions Router
REST API endpoints for project-scoped, user-isolated ContextDecision entities.
Preserves decision history and enforces strict supersession validation.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Project, ContextDecision, Conversation, utc_now
from backend.schemas import ContextDecisionCreate, ContextDecisionUpdate, ContextDecisionResponse
from backend.services.auth import get_current_user

router = APIRouter(prefix="/projects/{project_id}/decisions", tags=["Context Decisions"])


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


def _validate_superseded_by(
    superseded_by_id: Optional[str],
    project_id: str,
    current_decision_id: Optional[str],
    db: Session
) -> None:
    """Validate that a referenced superseding decision exists, belongs to the same project, and isn't self-referential."""
    if not superseded_by_id:
        return
    if current_decision_id and superseded_by_id == current_decision_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A decision cannot be superseded by itself."
        )
    replacement = db.query(ContextDecision).filter(ContextDecision.id == superseded_by_id).first()
    if not replacement:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid superseded_by_id: Referenced replacement decision does not exist."
        )
    if replacement.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid superseded_by_id: Replacement decision must belong to the same project."
        )


@router.post("", response_model=ContextDecisionResponse, status_code=status.HTTP_201_CREATED)
def create_decision(
    project_id: str,
    decision_in: ContextDecisionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new context decision for the specified project."""
    project = _verify_project_ownership(project_id, db, current_user)
    _validate_source_session(decision_in.source_session_id, project.id, db)
    _validate_superseded_by(decision_in.superseded_by_id, project.id, None, db)

    decision = ContextDecision(
        project_id=project.id,
        user_id=current_user.id,
        title=decision_in.title,
        description=decision_in.description,
        rationale=decision_in.rationale,
        category=decision_in.category or "architecture",
        status=decision_in.status or "accepted",
        source_session_id=decision_in.source_session_id,
        superseded_by_id=decision_in.superseded_by_id,
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision


@router.get("", response_model=List[ContextDecisionResponse])
def list_decisions(
    project_id: str,
    status: Optional[str] = Query(None, description="Filter by decision status"),
    category: Optional[str] = Query(None, description="Filter by decision category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all context decisions for the specified project with optional filtering."""
    project = _verify_project_ownership(project_id, db, current_user)

    query = db.query(ContextDecision).filter(ContextDecision.project_id == project.id)
    if status is not None:
        query = query.filter(ContextDecision.status == status)
    if category is not None:
        query = query.filter(ContextDecision.category == category)

    return query.order_by(ContextDecision.updated_at.desc()).all()


@router.get("/{decision_id}", response_model=ContextDecisionResponse)
def get_decision(
    project_id: str,
    decision_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a single context decision by ID within the specified project."""
    project = _verify_project_ownership(project_id, db, current_user)

    decision = db.query(ContextDecision).filter(
        ContextDecision.id == decision_id,
        ContextDecision.project_id == project.id,
    ).first()
    if not decision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision not found.")
    return decision


@router.patch("/{decision_id}", response_model=ContextDecisionResponse)
def update_decision(
    project_id: str,
    decision_id: str,
    decision_in: ContextDecisionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update attributes of a context decision.
    Preserves history and validates supersession references.
    """
    project = _verify_project_ownership(project_id, db, current_user)

    decision = db.query(ContextDecision).filter(
        ContextDecision.id == decision_id,
        ContextDecision.project_id == project.id,
    ).first()
    if not decision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision not found.")

    if decision_in.source_session_id is not None:
        _validate_source_session(decision_in.source_session_id, project.id, db)
        decision.source_session_id = decision_in.source_session_id

    if decision_in.superseded_by_id is not None:
        _validate_superseded_by(decision_in.superseded_by_id, project.id, decision.id, db)
        decision.superseded_by_id = decision_in.superseded_by_id

    if decision_in.title is not None:
        decision.title = decision_in.title
    if decision_in.description is not None:
        decision.description = decision_in.description
    if decision_in.rationale is not None:
        decision.rationale = decision_in.rationale
    if decision_in.category is not None:
        decision.category = decision_in.category
    if decision_in.status is not None:
        decision.status = decision_in.status

    decision.updated_at = utc_now()
    db.commit()
    db.refresh(decision)
    return decision


@router.delete("/{decision_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_decision(
    project_id: str,
    decision_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a context decision from the project."""
    project = _verify_project_ownership(project_id, db, current_user)

    decision = db.query(ContextDecision).filter(
        ContextDecision.id == decision_id,
        ContextDecision.project_id == project.id,
    ).first()
    if not decision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision not found.")

    db.delete(decision)
    db.commit()
    return None
