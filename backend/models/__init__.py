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
)
from sqlalchemy.orm import relationship
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
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")


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
