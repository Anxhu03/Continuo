"""
CONTINUO — Database Models Package
"""

import json
from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
    Integer,
    Boolean,
    Float,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, validates
from backend.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(32), default="user", nullable=False)  # 'user', 'developer', 'admin', 'support'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("ContextGoal", back_populates="user", cascade="all, delete-orphan")
    decisions = relationship("ContextDecision", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("ContextTask", back_populates="user", cascade="all, delete-orphan")
    technical_states = relationship("ContextTechnicalState", back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    current_version = Column(String(32), default="v1.0")
    health_score = Column(Float, default=85.0)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="projects")
    context_packages = relationship("ContextPackage", back_populates="project", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="project", cascade="all, delete-orphan")
    versions = relationship("ProjectVersion", back_populates="project", cascade="all, delete-orphan")
    handoffs = relationship("Handoff", back_populates="project", cascade="all, delete-orphan")
    goals = relationship("ContextGoal", back_populates="project", cascade="all, delete-orphan")
    decisions = relationship("ContextDecision", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("ContextTask", back_populates="project", cascade="all, delete-orphan")
    technical_states = relationship("ContextTechnicalState", back_populates="project", cascade="all, delete-orphan")


class ContextPackage(Base):
    __tablename__ = "context_packages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    version = Column(String(32), default="v1.0", nullable=False)
    
    # Structured context attributes
    objective = Column(Text, nullable=False)
    requirements_json = Column(Text, default="[]")       # list of requirements
    constraints_json = Column(Text, default="[]")        # list of constraints
    instructions_json = Column(Text, default="[]")       # critical instructions
    decisions_json = Column(Text, default="[]")          # architectural decisions
    current_state = Column(Text, nullable=False)
    completed_work_json = Column(Text, default="[]")     # finished tasks
    pending_work_json = Column(Text, default="[]")       # remaining tasks
    open_problems_json = Column(Text, default="[]")      # unresolved bugs / questions
    errors_json = Column(Text, default="[]")             # encountered error traces
    failed_attempts_json = Column(Text, default="[]")    # discarded approaches & why
    files_context_json = Column(Text, default="[]")      # relevant file paths & roles
    design_decisions_json = Column(Text, default="[]")   # UX/UI decisions
    dependencies_json = Column(Text, default="[]")       # libraries & services
    next_steps_json = Column(Text, default="[]")         # immediate next steps

    # Quality metrics
    quality_score = Column(Float, default=85.0)
    contradiction_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    project = relationship("Project", back_populates="context_packages")
    handoffs = relationship("Handoff", back_populates="context_package")

    # Helper properties for serializing / deserializing JSON fields
    def get_list(self, field_name: str) -> list:
        val = getattr(self, f"{field_name}_json", "[]")
        try:
            return json.loads(val) if val else []
        except Exception:
            return []

    def set_list(self, field_name: str, items: list) -> None:
        setattr(self, f"{field_name}_json", json.dumps(items or []))


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    provider = Column(String(64), nullable=False)       # 'chatgpt', 'claude', 'gemini', 'cursor'
    title = Column(String(255), nullable=True)
    raw_transcript = Column(Text, nullable=False)
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=utc_now)

    project = relationship("Project", back_populates="conversations")


class ProjectVersion(Base):
    __tablename__ = "project_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    version_number = Column(String(32), nullable=False)
    context_package_id = Column(String(36), nullable=False)
    changelog = Column(Text, nullable=True)
    diff_summary_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=utc_now)

    project = relationship("Project", back_populates="versions")


class Handoff(Base):
    __tablename__ = "handoffs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    context_package_id = Column(String(36), ForeignKey("context_packages.id"), nullable=False)
    source_provider = Column(String(64), nullable=False)
    destination_provider = Column(String(64), nullable=False)
    formatted_payload = Column(Text, nullable=False)
    status = Column(String(32), default="generated")  # 'generated', 'copied', 'opened'
    created_at = Column(DateTime, default=utc_now)

    project = relationship("Project", back_populates="handoffs")
    context_package = relationship("ContextPackage", back_populates="handoffs")


# =============================================================================
# PERSISTENT CONTEXT OS ENTITIES (Phase 9.2)
# =============================================================================

class ContextGoal(Base):
    __tablename__ = "context_goals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(64), default="goal", nullable=False)  # 'goal', 'requirement', 'constraint', 'instruction'
    status = Column(String(32), default="active", nullable=False)  # 'active', 'completed', 'abandoned', 'superseded'
    priority = Column(String(32), default="normal", nullable=False)  # 'critical', 'high', 'normal', 'low'
    source_session_id = Column(String(36), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    project = relationship("Project", back_populates="goals")
    user = relationship("User", back_populates="goals")
    source_session = relationship("Conversation", foreign_keys=[source_session_id])

    @validates("status")
    def validate_status(self, key, val):
        allowed = {"active", "completed", "abandoned", "superseded"}
        if val not in allowed:
            raise ValueError(f"Invalid goal status '{val}'. Must be one of {allowed}.")
        return val

    @validates("priority")
    def validate_priority(self, key, val):
        allowed = {"critical", "high", "normal", "low"}
        if val not in allowed:
            raise ValueError(f"Invalid priority '{val}'. Must be one of {allowed}.")
        return val


class ContextDecision(Base):
    __tablename__ = "context_decisions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rationale = Column(Text, nullable=True)
    category = Column(String(64), default="architecture", nullable=False)  # 'architecture', 'design_system', 'database', etc.
    status = Column(String(32), default="accepted", nullable=False)  # 'accepted', 'superseded', 'under_review', 'deprecated'
    source_session_id = Column(String(36), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    superseded_by_id = Column(String(36), ForeignKey("context_decisions.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    project = relationship("Project", back_populates="decisions")
    user = relationship("User", back_populates="decisions")
    source_session = relationship("Conversation", foreign_keys=[source_session_id])
    superseded_by = relationship("ContextDecision", remote_side=[id], foreign_keys=[superseded_by_id])

    @validates("status")
    def validate_status(self, key, val):
        allowed = {"accepted", "superseded", "under_review", "deprecated"}
        if val not in allowed:
            raise ValueError(f"Invalid decision status '{val}'. Must be one of {allowed}.")
        return val


class ContextTask(Base):
    __tablename__ = "context_tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(32), default="todo", nullable=False)  # 'todo', 'in_progress', 'blocked', 'completed', 'cancelled'
    priority = Column(String(32), default="normal", nullable=False)  # 'critical', 'high', 'normal', 'low'
    source_session_id = Column(String(36), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    project = relationship("Project", back_populates="tasks")
    user = relationship("User", back_populates="tasks")
    source_session = relationship("Conversation", foreign_keys=[source_session_id])

    @validates("status")
    def validate_status(self, key, val):
        allowed = {"todo", "in_progress", "blocked", "completed", "cancelled"}
        if val not in allowed:
            raise ValueError(f"Invalid task status '{val}'. Must be one of {allowed}.")
        return val

    @validates("priority")
    def validate_priority(self, key, val):
        allowed = {"critical", "high", "normal", "low"}
        if val not in allowed:
            raise ValueError(f"Invalid priority '{val}'. Must be one of {allowed}.")
        return val


class ContextTechnicalState(Base):
    __tablename__ = "context_technical_states"
    __table_args__ = (
        UniqueConstraint("project_id", "category", "key", name="uq_tech_state_project_cat_key"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(64), nullable=False)  # 'framework', 'runtime', 'renderer', 'database', etc.
    key = Column(String(128), nullable=False)
    value = Column(Text, nullable=False)
    source_session_id = Column(String(36), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    project = relationship("Project", back_populates="technical_states")
    user = relationship("User", back_populates="technical_states")
    source_session = relationship("Conversation", foreign_keys=[source_session_id])

