"""
CONTINUO — Pydantic Schemas Package
"""

from typing import List, Optional, Dict, Any
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
