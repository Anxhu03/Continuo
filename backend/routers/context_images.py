"""
CONTINUO — Context Images Router
REST API endpoints for project-scoped, user-isolated visual context assets.
Provides secure upload, metadata management, validation, and protected file streaming.
"""

import json
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    User,
    Project,
    ContextImage,
    ContextGoal,
    ContextTask,
    ContextTechnicalState,
    ContextPackage,
    ContextDecision,
    Conversation,
    generate_uuid,
    utc_now,
)
from backend.schemas import (
    ContextImageUpdate,
    ContextImageResponse,
    ContextImageType,
)
from backend.services.auth import get_current_user
from backend.services.storage import get_storage_provider
from backend.services.image_validator import process_and_validate_upload

router = APIRouter(prefix="/projects/{project_id}/images", tags=["Context Visual Assets"])

ALLOWED_IMAGE_TYPES = {
    "ui_screenshot",
    "design_reference",
    "character_reference",
    "blender_render",
    "moodboard",
    "diagram",
    "before_after",
    "ai_conversation_capture",
    "other",
}


def _verify_project_ownership(project_id: str, db: Session, current_user: User) -> Project:
    """Verify that the target project exists and belongs to the authenticated user."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You do not own this project.")
    return project


def _validate_image_associations(
    project_id: str,
    session_id: Optional[str],
    decision_ids: Optional[List[str]],
    context_ids: Optional[List[str]],
    db: Session,
) -> None:
    """Validate that all referenced session, decision, and context IDs belong to the project."""
    if session_id:
        conv = db.query(Conversation).filter(Conversation.id == session_id).first()
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid associated_session_id: Conversation session does not exist."
            )
        if conv.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid associated_session_id: Session does not belong to this project."
            )

    if decision_ids:
        for dec_id in decision_ids:
            dec = db.query(ContextDecision).filter(ContextDecision.id == dec_id).first()
            if not dec:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid associated_decision_id '{dec_id}': Decision does not exist."
                )
            if dec.project_id != project_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid associated_decision_id '{dec_id}': Decision does not belong to this project."
                )

    if context_ids:
        for ctx_id in context_ids:
            goal = db.query(ContextGoal).filter(ContextGoal.id == ctx_id, ContextGoal.project_id == project_id).first()
            task = db.query(ContextTask).filter(ContextTask.id == ctx_id, ContextTask.project_id == project_id).first()
            tech = db.query(ContextTechnicalState).filter(ContextTechnicalState.id == ctx_id, ContextTechnicalState.project_id == project_id).first()
            pkg = db.query(ContextPackage).filter(ContextPackage.id == ctx_id, ContextPackage.project_id == project_id).first()
            if not goal and not task and not tech and not pkg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid associated_context_id '{ctx_id}': Context does not exist or does not belong to this project."
                )


def _serialize_image(img: ContextImage, project_id: str) -> ContextImageResponse:
    """Convert ContextImage DB model into Pydantic response."""
    return ContextImageResponse(
        id=img.id,
        project_id=img.project_id,
        user_id=img.user_id,
        original_filename=img.original_filename,
        storage_key=img.storage_key,
        mime_type=img.mime_type,
        image_format=img.image_format,
        file_size=img.file_size,
        width=img.width,
        height=img.height,
        checksum_sha256=img.checksum_sha256,
        image_type=img.image_type,
        description=img.description,
        visual_tags=img.get_list("visual_tags"),
        associated_context_ids=img.get_list("associated_context_ids"),
        associated_decision_ids=img.get_list("associated_decision_ids"),
        associated_session_id=img.associated_session_id,
        file_url=f"/api/v1/projects/{project_id}/images/{img.id}/file",
        created_at=img.created_at,
        updated_at=img.updated_at,
    )


def _parse_json_list(raw_val: Optional[str], field_name: str) -> List[str]:
    """Parse a form string that might be a JSON array or comma-separated list."""
    if not raw_val:
        return []
    val = raw_val.strip()
    if val.startswith("[") and val.endswith("]"):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid JSON format for '{field_name}'."
            )
    return [x.strip() for x in val.split(",") if x.strip()]


@router.post("", response_model=ContextImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    project_id: str,
    file: UploadFile = File(...),
    image_type: Optional[str] = Form("other"),
    description: Optional[str] = Form(None),
    visual_tags: Optional[str] = Form(None),
    associated_context_ids: Optional[str] = Form(None),
    associated_decision_ids: Optional[str] = Form(None),
    associated_session_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload and register a visual context image for the project.
    Validates magic bytes, extracts dimensions and checksums, and safely stores the file.
    """
    project = _verify_project_ownership(project_id, db, current_user)

    # Validate image_type
    clean_type = (image_type or "other").strip().lower()
    if clean_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid image_type '{clean_type}'. Allowed: {sorted(ALLOWED_IMAGE_TYPES)}"
        )

    # Parse list form fields
    tags = _parse_json_list(visual_tags, "visual_tags")
    ctx_ids = _parse_json_list(associated_context_ids, "associated_context_ids")
    dec_ids = _parse_json_list(associated_decision_ids, "associated_decision_ids")
    clean_session_id = associated_session_id.strip() if associated_session_id else None

    # Validate associations against project
    _validate_image_associations(project.id, clean_session_id, dec_ids, ctx_ids, db)

    # Validate file and extract metadata deterministically
    validated = await process_and_validate_upload(file)

    # Generate unique ID and save to secure project-scoped storage
    image_id = generate_uuid()
    storage = get_storage_provider()
    storage_key = storage.save(
        project_id=project.id,
        file_id=image_id,
        safe_extension=validated.safe_extension,
        stream=validated.stream,
    )

    # Create DB record
    image_record = ContextImage(
        id=image_id,
        project_id=project.id,
        user_id=current_user.id,
        original_filename=validated.original_filename,
        storage_key=storage_key,
        mime_type=validated.mime_type,
        image_format=validated.image_format,
        file_size=validated.file_size,
        width=validated.width,
        height=validated.height,
        checksum_sha256=validated.checksum_sha256,
        image_type=clean_type,
        description=description,
        associated_session_id=clean_session_id,
    )
    image_record.set_list("visual_tags", tags)
    image_record.set_list("associated_context_ids", ctx_ids)
    image_record.set_list("associated_decision_ids", dec_ids)

    try:
        db.add(image_record)
        db.commit()
        db.refresh(image_record)
    except Exception:
        # Prevent orphan files if DB insertion fails
        db.rollback()
        storage.delete(storage_key)
        raise

    return _serialize_image(image_record, project.id)


@router.get("", response_model=List[ContextImageResponse])
def list_images(
    project_id: str,
    image_type: Optional[str] = Query(None, description="Filter by image type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all visual context images for the project, ordered by creation date."""
    project = _verify_project_ownership(project_id, db, current_user)

    query = db.query(ContextImage).filter(ContextImage.project_id == project.id)
    if image_type:
        query = query.filter(ContextImage.image_type == image_type.strip().lower())

    images = query.order_by(ContextImage.created_at.desc()).all()
    return [_serialize_image(img, project.id) for img in images]


@router.get("/{image_id}", response_model=ContextImageResponse)
def get_image_metadata(
    project_id: str,
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve metadata for a single visual context image."""
    project = _verify_project_ownership(project_id, db, current_user)

    img = db.query(ContextImage).filter(
        ContextImage.id == image_id,
        ContextImage.project_id == project.id,
    ).first()
    if not img:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")

    return _serialize_image(img, project.id)


@router.get("/{image_id}/file")
def get_image_file(
    project_id: str,
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Stream protected image file with verified MIME type and safe disposition headers.
    Protected: requires authentication and project ownership.
    """
    project = _verify_project_ownership(project_id, db, current_user)

    img = db.query(ContextImage).filter(
        ContextImage.id == image_id,
        ContextImage.project_id == project.id,
    ).first()
    if not img:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")

    storage = get_storage_provider()
    try:
        file_path = storage.get_path(img.storage_key)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image path error.")

    if not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image file not found on disk.")

    return FileResponse(
        path=str(file_path),
        media_type=img.mime_type,
        filename=img.original_filename,
    )


@router.patch("/{image_id}", response_model=ContextImageResponse)
def update_image_metadata(
    project_id: str,
    image_id: str,
    update_in: ContextImageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update metadata and context associations for an existing image."""
    project = _verify_project_ownership(project_id, db, current_user)

    img = db.query(ContextImage).filter(
        ContextImage.id == image_id,
        ContextImage.project_id == project.id,
    ).first()
    if not img:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")

    # Validate new associations if provided
    _validate_image_associations(
        project_id=project.id,
        session_id=update_in.associated_session_id if update_in.associated_session_id is not None else img.associated_session_id,
        decision_ids=update_in.associated_decision_ids if update_in.associated_decision_ids is not None else img.get_list("associated_decision_ids"),
        context_ids=update_in.associated_context_ids if update_in.associated_context_ids is not None else img.get_list("associated_context_ids"),
        db=db,
    )

    if update_in.image_type is not None:
        img.image_type = update_in.image_type
    if update_in.description is not None:
        img.description = update_in.description
    if update_in.visual_tags is not None:
        img.set_list("visual_tags", update_in.visual_tags)
    if update_in.associated_context_ids is not None:
        img.set_list("associated_context_ids", update_in.associated_context_ids)
    if update_in.associated_decision_ids is not None:
        img.set_list("associated_decision_ids", update_in.associated_decision_ids)
    if update_in.associated_session_id is not None:
        img.associated_session_id = update_in.associated_session_id

    img.updated_at = utc_now()
    db.commit()
    db.refresh(img)
    return _serialize_image(img, project.id)


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(
    project_id: str,
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete image database record and associated physical file from storage."""
    project = _verify_project_ownership(project_id, db, current_user)

    img = db.query(ContextImage).filter(
        ContextImage.id == image_id,
        ContextImage.project_id == project.id,
    ).first()
    if not img:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")

    storage = get_storage_provider()
    storage_key = img.storage_key

    # Delete DB record first, then remove physical file
    db.delete(img)
    db.commit()

    # Safely remove physical file
    storage.delete(storage_key)

    return None
