"""
CONTINUO — Pydantic Schemas Package
"""

from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

# -----------------------------------------------------------------------------
# Auth Schemas
# -----------------------------------------------------------------------------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None
    role: Optional[str] = "user"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str = "user"

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: Optional[str] = None
    role: str = "user"
    created_at: datetime

class DiagnosticsResponse(BaseModel):
    status: str
    role: str
    gateway_port: int
    database: str
    active_users: int
    active_projects: int
    total_context_packages: int
    version: str
    features: Dict[str, Any]

# -----------------------------------------------------------------------------
# Project Schemas
# -----------------------------------------------------------------------------
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    initial_objective: Optional[str] = Field(None, max_length=2000)

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    current_version: Optional[str] = None

class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    current_version: str
    health_score: float
    created_at: datetime
    updated_at: datetime

# -----------------------------------------------------------------------------
# Context Package Schemas
# -----------------------------------------------------------------------------
class ContextPackageData(BaseModel):
    objective: str
    requirements: List[str] = []
    constraints: List[str] = []
    instructions: List[str] = []
    decisions: List[str] = []
    current_state: str
    completed_work: List[str] = []
    pending_work: List[str] = []
    open_problems: List[str] = []
    errors: List[str] = []
    failed_attempts: List[str] = []
    files_context: List[str] = []
    design_decisions: List[str] = []
    dependencies: List[str] = []
    next_steps: List[str] = []

class ContextPackageCreate(ContextPackageData):
    project_id: str
    version: Optional[str] = "v1.0"

class ContextPackageUpdate(BaseModel):
    objective: Optional[str] = None
    requirements: Optional[List[str]] = None
    constraints: Optional[List[str]] = None
    instructions: Optional[List[str]] = None
    decisions: Optional[List[str]] = None
    current_state: Optional[str] = None
    completed_work: Optional[List[str]] = None
    pending_work: Optional[List[str]] = None
    open_problems: Optional[List[str]] = None
    errors: Optional[List[str]] = None
    failed_attempts: Optional[List[str]] = None
    files_context: Optional[List[str]] = None
    design_decisions: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    next_steps: Optional[List[str]] = None
    version: Optional[str] = None

class ContextPackageResponse(ContextPackageData):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    version: str
    quality_score: float
    contradiction_count: int
    created_at: datetime
    updated_at: datetime

# -----------------------------------------------------------------------------
# Context Ingestion / Capture Request
# -----------------------------------------------------------------------------
class ContextCaptureRequest(BaseModel):
    project_id: str
    provider: str = "chatgpt" # chatgpt, claude, gemini, cursor
    raw_transcript: str = Field(..., min_length=10, max_length=500000)
    title: Optional[str] = Field(None, max_length=200)

class ContextAnalyzeRequest(BaseModel):
    raw_transcript: str = Field(..., min_length=10, max_length=500000)
    provider: Optional[str] = "chatgpt"

# -----------------------------------------------------------------------------
# Quality & Contradiction Schemas
# -----------------------------------------------------------------------------
class ContradictionItem(BaseModel):
    severity: str # 'warning', 'critical'
    topic: str
    earlier_statement: str
    later_statement: str
    explanation: str

class QualityScoreResponse(BaseModel):
    overall_score: float
    breakdown: Dict[str, float]
    contradictions: List[ContradictionItem] = []
    recommendations: List[str] = []

# -----------------------------------------------------------------------------
# Diff & Versioning Schemas
# -----------------------------------------------------------------------------
class ContextDiffResponse(BaseModel):
    project_id: str
    from_version: str
    to_version: str
    added: Dict[str, List[str]]
    modified: Dict[str, Dict[str, str]]
    removed: Dict[str, List[str]]
    summary: str

class ProjectVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    version_number: str
    context_package_id: str
    changelog: Optional[str] = None
    created_at: datetime

# -----------------------------------------------------------------------------
# Handoff Schemas
# -----------------------------------------------------------------------------
class HandoffCreateRequest(BaseModel):
    project_id: str
    context_package_id: Optional[str] = None
    source_provider: str = "chatgpt"
    destination_provider: str = "claude" # claude, chatgpt, gemini, cursor
    custom_instructions: Optional[str] = Field(None, max_length=5000)

class HandoffResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    context_package_id: str
    source_provider: str
    destination_provider: str
    formatted_payload: str
    destination_url: str
    status: str
    created_at: datetime

# -----------------------------------------------------------------------------
# Context OS Schemas (Phase 9.2)
# -----------------------------------------------------------------------------

# Context Goal Schemas
class ContextGoalCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field("goal", max_length=64)
    status: Optional[Literal["active", "completed", "abandoned", "superseded"]] = "active"
    priority: Optional[Literal["critical", "high", "normal", "low"]] = "normal"
    source_session_id: Optional[str] = None

class ContextGoalUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=64)
    status: Optional[Literal["active", "completed", "abandoned", "superseded"]] = None
    priority: Optional[Literal["critical", "high", "normal", "low"]] = None
    source_session_id: Optional[str] = None

class ContextGoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    user_id: str
    title: str
    description: Optional[str] = None
    category: str
    status: str
    priority: str
    source_session_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# Context Decision Schemas
class ContextDecisionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    rationale: Optional[str] = None
    category: Optional[str] = Field("architecture", max_length=64)
    status: Optional[Literal["accepted", "superseded", "under_review", "deprecated"]] = "accepted"
    source_session_id: Optional[str] = None
    superseded_by_id: Optional[str] = None

class ContextDecisionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    rationale: Optional[str] = None
    category: Optional[str] = Field(None, max_length=64)
    status: Optional[Literal["accepted", "superseded", "under_review", "deprecated"]] = None
    source_session_id: Optional[str] = None
    superseded_by_id: Optional[str] = None

class ContextDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    user_id: str
    title: str
    description: Optional[str] = None
    rationale: Optional[str] = None
    category: str
    status: str
    source_session_id: Optional[str] = None
    superseded_by_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# Context Task Schemas
class ContextTaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[Literal["todo", "in_progress", "blocked", "completed", "cancelled"]] = "todo"
    priority: Optional[Literal["critical", "high", "normal", "low"]] = "normal"
    source_session_id: Optional[str] = None
    completed_at: Optional[datetime] = None

class ContextTaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[Literal["todo", "in_progress", "blocked", "completed", "cancelled"]] = None
    priority: Optional[Literal["critical", "high", "normal", "low"]] = None
    source_session_id: Optional[str] = None
    completed_at: Optional[datetime] = None

class ContextTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    user_id: str
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    source_session_id: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# Context Technical State Schemas
class ContextTechnicalStateCreate(BaseModel):
    category: str = Field(..., min_length=1, max_length=64)
    key: str = Field(..., min_length=1, max_length=128)
    value: str
    source_session_id: Optional[str] = None

class ContextTechnicalStateUpdate(BaseModel):
    category: Optional[str] = Field(None, min_length=1, max_length=64)
    key: Optional[str] = Field(None, min_length=1, max_length=128)
    value: Optional[str] = None
    source_session_id: Optional[str] = None

class ContextTechnicalStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    user_id: str
    category: str
    key: str
    value: str
    source_session_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------------------
# Context Image Schemas (Phase 9.4)
# -----------------------------------------------------------------------------
ContextImageType = Literal[
    "ui_screenshot",
    "design_reference",
    "character_reference",
    "blender_render",
    "moodboard",
    "diagram",
    "before_after",
    "ai_conversation_capture",
    "other"
]

class ContextImageUpdate(BaseModel):
    image_type: Optional[ContextImageType] = None
    description: Optional[str] = None
    visual_tags: Optional[List[str]] = None
    associated_context_ids: Optional[List[str]] = None
    associated_decision_ids: Optional[List[str]] = None
    associated_session_id: Optional[str] = None

class ContextImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    user_id: str
    original_filename: str
    storage_key: str
    mime_type: str
    image_format: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    checksum_sha256: str
    image_type: str
    description: Optional[str] = None
    visual_tags: List[str] = []
    associated_context_ids: List[str] = []
    associated_decision_ids: List[str] = []
    associated_session_id: Optional[str] = None
    file_url: str
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------------------
# Context Extraction Intelligence Schemas (Phase 9.5)
# -----------------------------------------------------------------------------

class ExtractedGoalCandidate(BaseModel):
    title: str
    description: Optional[str] = None
    category: str = "goal"  # 'goal', 'requirement', 'constraint', 'instruction'
    priority: Literal["critical", "high", "normal", "low"] = "normal"
    confidence: float = 0.9
    explicit: bool = True


class ExtractedDecisionCandidate(BaseModel):
    title: str
    description: Optional[str] = None
    rationale: Optional[str] = None
    category: str = "architecture"
    status: Literal["accepted", "superseded", "under_review", "deprecated"] = "accepted"
    confidence: float = 0.9
    explicit: bool = True


class ExtractedTaskCandidate(BaseModel):
    title: str
    description: Optional[str] = None
    status: Literal["todo", "in_progress", "blocked", "completed", "cancelled"] = "todo"
    priority: Literal["critical", "high", "normal", "low"] = "normal"
    confidence: float = 0.9
    explicit: bool = True


class ExtractedTechStateCandidate(BaseModel):
    category: str
    key: str
    value: str
    confidence: float = 0.9
    explicit: bool = True


class ExtractedVisualReferenceCandidate(BaseModel):
    detected_image_id: Optional[str] = None
    original_filename: Optional[str] = None
    detected_role: str = "other"  # ContextImageType
    description: Optional[str] = None
    visual_tags: List[str] = []
    associated_goal_titles: List[str] = []
    associated_decision_titles: List[str] = []
    associated_task_titles: List[str] = []
    confidence: float = 0.85
    explicit: bool = True


class StructuredExtractionResult(BaseModel):
    goals: List[ExtractedGoalCandidate] = []
    decisions: List[ExtractedDecisionCandidate] = []
    tasks: List[ExtractedTaskCandidate] = []
    technical_states: List[ExtractedTechStateCandidate] = []
    visual_references: List[ExtractedVisualReferenceCandidate] = []
    design_context: List[str] = []
    project_state: Optional[str] = None
    confidence_summary: Dict[str, float] = {}
    contradictions: List[ContradictionItem] = []


class ExtractContextOSRequest(BaseModel):
    raw_transcript: str = Field(..., min_length=1, max_length=500000)
    auto_persist: bool = False
    session_id: Optional[str] = None


class ExtractContextOSResponse(BaseModel):
    extracted: StructuredExtractionResult
    persisted_counts: Dict[str, int] = {}

