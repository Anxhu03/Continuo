"""
CONTINUO — AI Handoff Router
Generates cross-AI continuation packages with verified destination links and honest transport boundaries.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Project, ContextPackage, Handoff
from backend.schemas import HandoffCreateRequest, HandoffResponse
from backend.services.auth import get_current_user
from backend.services.handoff_generator import HandoffService

router = APIRouter(prefix="/handoffs", tags=["AI Handoff"])

@router.post("", response_model=HandoffResponse, status_code=status.HTTP_201_CREATED)
def create_handoff(
    handoff_in: HandoffCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate an optimized cross-AI continuation package for Claude, ChatGPT, Gemini, or Cursor.
    Provides verified payload and clean direct destination navigation.
    """
    project = db.query(Project).filter(Project.id == handoff_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this project.")

    # Fetch targeted or latest ContextPackage
    if handoff_in.context_package_id:
        pkg = db.query(ContextPackage).filter(ContextPackage.id == handoff_in.context_package_id).first()
    else:
        pkg = (
            db.query(ContextPackage)
            .filter(ContextPackage.project_id == project.id)
            .order_by(ContextPackage.created_at.desc())
            .first()
        )

    if not pkg:
        raise HTTPException(status_code=404, detail="No ContextPackage found to generate handoff from.")

    context_dict = {
        "version": pkg.version,
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

    result = HandoffService.generate(
        context_dict,
        project_name=project.name,
        destination_provider=handoff_in.destination_provider,
        custom_instructions=handoff_in.custom_instructions
    )

    handoff = Handoff(
        project_id=project.id,
        context_package_id=pkg.id,
        source_provider=handoff_in.source_provider,
        destination_provider=result["provider"],
        formatted_payload=result["formatted_payload"],
        status="generated"
    )
    db.add(handoff)
    db.commit()
    db.refresh(handoff)

    return HandoffResponse(
        id=handoff.id,
        project_id=handoff.project_id,
        context_package_id=handoff.context_package_id,
        source_provider=handoff.source_provider,
        destination_provider=handoff.destination_provider,
        formatted_payload=handoff.formatted_payload,
        destination_url=result["destination_url"],
        status=handoff.status,
        created_at=handoff.created_at
    )

@router.get("/projects/{project_id}", response_model=List[HandoffResponse])
def list_project_handoffs(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve history of handoffs generated for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this project.")

    handoffs = (
        db.query(Handoff)
        .filter(Handoff.project_id == project_id)
        .order_by(Handoff.created_at.desc())
        .limit(20)
        .all()
    )

    responses = []
    for h in handoffs:
        from backend.services.handoff_generator import PROVIDER_URLS
        dest_url = PROVIDER_URLS.get(h.destination_provider.lower(), "https://claude.ai/new")
        responses.append(
            HandoffResponse(
                id=h.id,
                project_id=h.project_id,
                context_package_id=h.context_package_id,
                source_provider=h.source_provider,
                destination_provider=h.destination_provider,
                formatted_payload=h.formatted_payload,
                destination_url=dest_url,
                status=h.status,
                created_at=h.created_at
            )
        )
    return responses
