"""
CONTINUO — Context Engine & Package Router
Endpoints for dialogue capture, structured context extraction, manual curation, and quality analysis.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Project, ContextPackage, Conversation, ProjectVersion
from backend.schemas import (
    ContextCaptureRequest,
    ContextAnalyzeRequest,
    ContextPackageResponse,
    ContextPackageUpdate,
    QualityScoreResponse,
    ExtractContextOSRequest,
    ExtractContextOSResponse,
    StructuredExtractionResult,
)
from backend.services.auth import get_current_user, get_optional_user
from backend.services.context_engine import ContextEngine
from backend.services.context_extraction import ContextExtractionService
from backend.services.quality_scorer import QualityScorer
from backend.services.contradiction import ContradictionDetector

router = APIRouter(prefix="/context", tags=["Context Engine"])

def serialize_context_package(pkg: ContextPackage) -> ContextPackageResponse:
    """Helper to convert ContextPackage DB model to Pydantic response with deserialized lists."""
    return ContextPackageResponse(
        id=pkg.id,
        project_id=pkg.project_id,
        version=pkg.version,
        objective=pkg.objective,
        requirements=pkg.get_list("requirements"),
        constraints=pkg.get_list("constraints"),
        instructions=pkg.get_list("instructions"),
        decisions=pkg.get_list("decisions"),
        current_state=pkg.current_state,
        completed_work=pkg.get_list("completed_work"),
        pending_work=pkg.get_list("pending_work"),
        open_problems=pkg.get_list("open_problems"),
        errors=pkg.get_list("errors"),
        failed_attempts=pkg.get_list("failed_attempts"),
        files_context=pkg.get_list("files_context"),
        design_decisions=pkg.get_list("design_decisions"),
        dependencies=pkg.get_list("dependencies"),
        next_steps=pkg.get_list("next_steps"),
        quality_score=pkg.quality_score,
        contradiction_count=pkg.contradiction_count,
        created_at=pkg.created_at,
        updated_at=pkg.updated_at
    )

@router.post("/analyze", response_model=Dict[str, Any])
def analyze_context(request: ContextAnalyzeRequest):
    """
    Stateless inspection: extracts structured context and calculates real quality score
    without requiring persistence. Perfect for playground and extension live preview.
    """
    extracted = ContextEngine.extract(request.raw_transcript)
    quality = QualityScorer.evaluate(extracted)
    return {
        "extracted_context": extracted,
        "quality": quality,
        "provider": request.provider
    }

@router.post("/extract-os", response_model=ExtractContextOSResponse)
def extract_stateless_context_os(
    request: ExtractContextOSRequest,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Phase 9.5: Stateless extraction of Context OS entities (Goals, Decisions, Tasks,
    Technical States, Design Context, Visual References) without persistence.
    """
    extracted_os = ContextExtractionService.extract(
        raw_text=request.raw_transcript,
        session_id=request.session_id
    )
    return ExtractContextOSResponse(
        extracted=extracted_os,
        persisted_counts={}
    )

@router.post("/projects/{project_id}/extract-os", response_model=ExtractContextOSResponse)
def extract_project_context_os(
    project_id: str,
    request: ExtractContextOSRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Phase 9.5: Project-scoped extraction of Context OS entities with visual asset linking.
    If auto_persist=True, persists validated, deduplicated entities to project memory.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this project.")

    extracted_os = ContextExtractionService.extract(
        raw_text=request.raw_transcript,
        project_name=project.name,
        project_id=project.id,
        current_user_id=current_user.id,
        db=db,
        session_id=request.session_id
    )

    persisted_counts = {}
    if request.auto_persist:
        persisted_counts = ContextExtractionService.persist_extracted_context(
            extracted=extracted_os,
            project=project,
            user=current_user,
            db=db,
            session_id=request.session_id
        )

    return ExtractContextOSResponse(
        extracted=extracted_os,
        persisted_counts=persisted_counts
    )

@router.post("/capture", response_model=ContextPackageResponse, status_code=status.HTTP_201_CREATED)
def capture_context(
    capture_in: ContextCaptureRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ingest a raw AI conversation transcript, execute the Context Engine pipeline,
    evaluate quality, persist the structured ContextPackage, advance project memory,
    and synthesize persistent Context OS entities (Phase 9.5).
    """
    project = db.query(Project).filter(Project.id == capture_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this project.")

    # 1. Run extraction pipeline
    extracted = ContextEngine.extract(capture_in.raw_transcript, project_name=project.name)

    # 2. Run quality scoring & contradiction analysis
    quality_analysis = QualityScorer.evaluate(extracted)
    score = quality_analysis["overall_score"]
    contradiction_count = len(quality_analysis["contradictions"])

    # 3. Calculate next version number (e.g. v1.0 -> v1.1)
    current_ver = project.current_version or "v1.0"
    try:
        ver_num = float(current_ver.replace("v", ""))
        next_ver = f"v{round(ver_num + 0.1, 1)}"
    except Exception:
        next_ver = "v1.1"

    # 4. Create new ContextPackage record
    pkg = ContextPackage(
        project_id=project.id,
        version=next_ver,
        objective=extracted["objective"],
        current_state=extracted["current_state"],
        quality_score=score,
        contradiction_count=contradiction_count
    )
    for field in [
        "requirements", "constraints", "instructions", "decisions",
        "completed_work", "pending_work", "open_problems", "errors",
        "failed_attempts", "files_context", "design_decisions",
        "dependencies", "next_steps"
    ]:
        pkg.set_list(field, extracted.get(field, []))

    db.add(pkg)
    db.commit()
    db.refresh(pkg)

    # 5. Record raw conversation transcript reference
    conv = Conversation(
        project_id=project.id,
        provider=capture_in.provider,
        title=capture_in.title or f"Capture from {capture_in.provider.title()}",
        raw_transcript=capture_in.raw_transcript
    )
    db.add(conv)
    db.flush()

    # 5b. Phase 9.5: Extract and persist structured Context OS entities (Goals, Decisions, Tasks, Technical States, Visual Links)
    try:
        extracted_os = ContextExtractionService.extract(
            raw_text=capture_in.raw_transcript,
            project_name=project.name,
            project_id=project.id,
            current_user_id=current_user.id,
            db=db,
            session_id=conv.id
        )
        ContextExtractionService.persist_extracted_context(
            extracted=extracted_os,
            project=project,
            user=current_user,
            db=db,
            session_id=conv.id
        )
    except Exception:
        # Fallback safeguard: extraction failure should not break legacy capture flow
        pass

    # 6. Update Project record state
    project.current_version = next_ver
    project.health_score = score
    
    # 7. Record new ProjectVersion milestone
    p_version = ProjectVersion(
        project_id=project.id,
        version_number=next_ver,
        context_package_id=pkg.id,
        changelog=f"Ingested context from {capture_in.provider.title()}; updated current state to {next_ver}."
    )
    db.add(p_version)

    db.commit()
    db.refresh(pkg)

    return serialize_context_package(pkg)

@router.get("/projects/{project_id}/context", response_model=ContextPackageResponse)
def get_project_context(
    project_id: str,
    version: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve active or specific versioned ContextPackage for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this project.")

    query = db.query(ContextPackage).filter(ContextPackage.project_id == project_id)
    if version:
        pkg = query.filter(ContextPackage.version == version).first()
    else:
        pkg = query.order_by(ContextPackage.created_at.desc()).first()

    if not pkg:
        raise HTTPException(status_code=404, detail="No ContextPackage found for this project.")

    return serialize_context_package(pkg)

@router.patch("/projects/{project_id}/context", response_model=ContextPackageResponse)
def update_project_context(
    project_id: str,
    update_in: ContextPackageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Allow the user to manually curate and edit context fields (human control).
    Automatically recalculates quality and registers an updated context version.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this project.")

    latest_pkg = (
        db.query(ContextPackage)
        .filter(ContextPackage.project_id == project_id)
        .order_by(ContextPackage.created_at.desc())
        .first()
    )
    if not latest_pkg:
        raise HTTPException(status_code=404, detail="No ContextPackage found to update.")

    # Prepare dict of existing data and apply updates
    data = {
        "objective": update_in.objective if update_in.objective is not None else latest_pkg.objective,
        "current_state": update_in.current_state if update_in.current_state is not None else latest_pkg.current_state,
        "requirements": update_in.requirements if update_in.requirements is not None else latest_pkg.get_list("requirements"),
        "constraints": update_in.constraints if update_in.constraints is not None else latest_pkg.get_list("constraints"),
        "instructions": update_in.instructions if update_in.instructions is not None else latest_pkg.get_list("instructions"),
        "decisions": update_in.decisions if update_in.decisions is not None else latest_pkg.get_list("decisions"),
        "completed_work": update_in.completed_work if update_in.completed_work is not None else latest_pkg.get_list("completed_work"),
        "pending_work": update_in.pending_work if update_in.pending_work is not None else latest_pkg.get_list("pending_work"),
        "open_problems": update_in.open_problems if update_in.open_problems is not None else latest_pkg.get_list("open_problems"),
        "errors": update_in.errors if update_in.errors is not None else latest_pkg.get_list("errors"),
        "failed_attempts": update_in.failed_attempts if update_in.failed_attempts is not None else latest_pkg.get_list("failed_attempts"),
        "files_context": update_in.files_context if update_in.files_context is not None else latest_pkg.get_list("files_context"),
        "design_decisions": update_in.design_decisions if update_in.design_decisions is not None else latest_pkg.get_list("design_decisions"),
        "dependencies": update_in.dependencies if update_in.dependencies is not None else latest_pkg.get_list("dependencies"),
        "next_steps": update_in.next_steps if update_in.next_steps is not None else latest_pkg.get_list("next_steps"),
    }

    # Recalculate quality
    eval_result = QualityScorer.evaluate(data)
    new_score = eval_result["overall_score"]
    contra_count = len(eval_result["contradictions"])

    # Increment version
    try:
        ver_num = float(latest_pkg.version.replace("v", ""))
        next_ver = f"v{round(ver_num + 0.1, 1)}"
    except Exception:
        next_ver = "v1.1"

    new_pkg = ContextPackage(
        project_id=project_id,
        version=next_ver,
        objective=data["objective"],
        current_state=data["current_state"],
        quality_score=new_score,
        contradiction_count=contra_count
    )
    for k, v in data.items():
        if k not in ["objective", "current_state"]:
            new_pkg.set_list(k, v)

    db.add(new_pkg)
    db.commit()
    db.refresh(new_pkg)

    project.current_version = next_ver
    project.health_score = new_score

    p_ver = ProjectVersion(
        project_id=project_id,
        version_number=next_ver,
        context_package_id=new_pkg.id,
        changelog="User curated and modified Context Package in Project Memory Editor."
    )
    db.add(p_ver)
    db.commit()

    return serialize_context_package(new_pkg)

@router.patch("/{context_id}", response_model=ContextPackageResponse)
def update_context_by_id(
    context_id: str,
    update_in: ContextPackageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update context package directly by context package ID."""
    pkg = db.query(ContextPackage).filter(ContextPackage.id == context_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="ContextPackage not found.")
    project = db.query(Project).filter(Project.id == pkg.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this project.")
    return update_project_context(project.id, update_in, db, current_user)

