"""initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-15 06:00:00.000000

"""
from typing import Sequence, Union
import logging
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger("alembic.runtime.migration")

def relation_or_type_exists(bind, name: str) -> bool:
    """Check if table, view, composite type, or enum relation exists in the database.
    
    Specifically guards against PostgreSQL collision on pg_type_typname_nsp_index:
    Key (typname, typnamespace)=(<name>, 2200) already exists.
    """
    inspector = inspect(bind)
    existing = set()
    try:
        existing.update(inspector.get_table_names(schema="public"))
    except Exception:
        pass
    try:
        existing.update(inspector.get_table_names())
    except Exception:
        pass
    try:
        existing.update(inspector.get_view_names(schema="public"))
    except Exception:
        pass
    try:
        existing.update(inspector.get_view_names())
    except Exception:
        pass
    if name in existing:
        return True

    # PostgreSQL specific catalog inspection
    if bind.dialect.name == "postgresql":
        try:
            # Check pg_class (regular tables, views, foreign tables, composite relations)
            res_class = bind.execute(text(
                "SELECT 1 FROM pg_class c "
                "JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE c.relname = :name AND n.nspname IN ('public', current_schema())"
            ), {"name": name}).scalar()
            if res_class:
                return True
        except Exception as e:
            logger.warning(f"Error checking pg_class for relation {name}: {e}")

        try:
            # Check pg_type (table composite row-types, custom enums, domains)
            # Directly prevents duplicate key violation on pg_type_typname_nsp_index (typname, typnamespace)
            res_type = bind.execute(text(
                "SELECT 1 FROM pg_type t "
                "JOIN pg_namespace n ON n.oid = t.typnamespace "
                "WHERE t.typname = :name AND n.nspname IN ('public', current_schema())"
            ), {"name": name}).scalar()
            if res_type:
                return True
        except Exception as e:
            logger.warning(f"Error checking pg_type for type {name}: {e}")

    return False

def index_exists(bind, table_name: str, index_name: str) -> bool:
    """Check if index exists on the given table."""
    inspector = inspect(bind)
    try:
        for idx in inspector.get_indexes(table_name):
            if idx.get("name") == index_name:
                return True
    except Exception:
        pass

    if bind.dialect.name == "postgresql":
        try:
            res = bind.execute(text(
                "SELECT 1 FROM pg_indexes WHERE (schemaname IN ('public', current_schema())) "
                "AND tablename = :table_name AND indexname = :index_name"
            ), {"table_name": table_name, "index_name": index_name}).scalar()
            if res:
                return True
        except Exception:
            pass

    return False

def safe_create_index(bind, index_name: str, table_name: str, columns: list, unique: bool = False) -> None:
    """Create index if it does not already exist."""
    if not index_exists(bind, table_name, index_name):
        try:
            op.create_index(index_name, table_name, columns, unique=unique)
            logger.info(f"Created index: {index_name} on {table_name}")
        except Exception as e:
            logger.warning(f"Could not create index {index_name} (may already exist): {e}")
    else:
        logger.info(f"Index '{index_name}' already exists on '{table_name}'; preserving.")

def upgrade() -> None:
    bind = op.get_bind()

    # 1. users table
    if not relation_or_type_exists(bind, "users"):
        op.create_table(
            "users",
            sa.Column("id", sa.String(36), primary_key=True, nullable=False),
            sa.Column("email", sa.String(255), nullable=False),
            sa.Column("hashed_password", sa.String(255), nullable=False),
            sa.Column("full_name", sa.String(255), nullable=True),
            sa.Column("role", sa.String(32), nullable=False, server_default="user"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        safe_create_index(bind, "ix_users_email", "users", ["email"], unique=True)
        logger.info("Created table: users")
    else:
        logger.info("Table or type 'users' already exists in namespace; preserving existing structure and data.")
        safe_create_index(bind, "ix_users_email", "users", ["email"], unique=True)

    # 2. projects table
    if not relation_or_type_exists(bind, "projects"):
        op.create_table(
            "projects",
            sa.Column("id", sa.String(36), primary_key=True, nullable=False),
            sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("current_version", sa.String(32), nullable=False, server_default="v1.0"),
            sa.Column("health_score", sa.Float(), nullable=False, server_default="85.0"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        safe_create_index(bind, "ix_projects_user_id", "projects", ["user_id"])
        logger.info("Created table: projects")
    else:
        logger.info("Table or type 'projects' already exists; preserving existing structure and data.")
        safe_create_index(bind, "ix_projects_user_id", "projects", ["user_id"])

    # 3. context_packages table
    if not relation_or_type_exists(bind, "context_packages"):
        op.create_table(
            "context_packages",
            sa.Column("id", sa.String(36), primary_key=True, nullable=False),
            sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
            sa.Column("version", sa.String(32), nullable=False, server_default="v1.0"),
            sa.Column("objective", sa.Text(), nullable=False),
            sa.Column("requirements_json", sa.Text(), nullable=True, server_default="[]"),
            sa.Column("constraints_json", sa.Text(), nullable=True, server_default="[]"),
            sa.Column("instructions_json", sa.Text(), nullable=True, server_default="[]"),
            sa.Column("decisions_json", sa.Text(), nullable=True, server_default="[]"),
            sa.Column("current_state", sa.Text(), nullable=False),
            sa.Column("completed_work_json", sa.Text(), nullable=True, server_default="[]"),
            sa.Column("pending_work_json", sa.Text(), nullable=True, server_default="[]"),
            sa.Column("open_problems_json", sa.Text(), nullable=True, server_default="[]"),
            sa.Column("errors_json", sa.Text(), nullable=True, server_default="[]"),
            sa.Column("failed_attempts_json", sa.Text(), nullable=True, server_default="[]"),
            sa.Column("files_context_json", sa.Text(), nullable=True, server_default="[]"),
            sa.Column("design_decisions_json", sa.Text(), nullable=True, server_default="[]"),
            sa.Column("dependencies_json", sa.Text(), nullable=True, server_default="[]"),
            sa.Column("next_steps_json", sa.Text(), nullable=True, server_default="[]"),
            sa.Column("quality_score", sa.Float(), nullable=False, server_default="85.0"),
            sa.Column("contradiction_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        safe_create_index(bind, "ix_context_packages_project_id", "context_packages", ["project_id"])
        logger.info("Created table: context_packages")
    else:
        logger.info("Table or type 'context_packages' already exists; preserving existing structure and data.")
        safe_create_index(bind, "ix_context_packages_project_id", "context_packages", ["project_id"])

    # 4. conversations table
    if not relation_or_type_exists(bind, "conversations"):
        op.create_table(
            "conversations",
            sa.Column("id", sa.String(36), primary_key=True, nullable=False),
            sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
            sa.Column("provider", sa.String(64), nullable=False),
            sa.Column("title", sa.String(255), nullable=True),
            sa.Column("raw_transcript", sa.Text(), nullable=False),
            sa.Column("metadata_json", sa.Text(), nullable=True, server_default="{}"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        safe_create_index(bind, "ix_conversations_project_id", "conversations", ["project_id"])
        logger.info("Created table: conversations")
    else:
        logger.info("Table or type 'conversations' already exists; preserving existing structure and data.")
        safe_create_index(bind, "ix_conversations_project_id", "conversations", ["project_id"])

    # 5. project_versions table
    if not relation_or_type_exists(bind, "project_versions"):
        op.create_table(
            "project_versions",
            sa.Column("id", sa.String(36), primary_key=True, nullable=False),
            sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
            sa.Column("version_number", sa.String(32), nullable=False),
            sa.Column("context_package_id", sa.String(36), nullable=False),
            sa.Column("changelog", sa.Text(), nullable=True),
            sa.Column("diff_summary_json", sa.Text(), nullable=True, server_default="{}"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        safe_create_index(bind, "ix_project_versions_project_id", "project_versions", ["project_id"])
        logger.info("Created table: project_versions")
    else:
        logger.info("Table or type 'project_versions' already exists; preserving existing structure and data.")
        safe_create_index(bind, "ix_project_versions_project_id", "project_versions", ["project_id"])

    # 6. handoffs table
    if not relation_or_type_exists(bind, "handoffs"):
        op.create_table(
            "handoffs",
            sa.Column("id", sa.String(36), primary_key=True, nullable=False),
            sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
            sa.Column("context_package_id", sa.String(36), sa.ForeignKey("context_packages.id", ondelete="CASCADE"), nullable=False),
            sa.Column("source_provider", sa.String(64), nullable=False),
            sa.Column("destination_provider", sa.String(64), nullable=False),
            sa.Column("formatted_payload", sa.Text(), nullable=False),
            sa.Column("status", sa.String(32), nullable=False, server_default="generated"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        safe_create_index(bind, "ix_handoffs_project_id", "handoffs", ["project_id"])
        logger.info("Created table: handoffs")
    else:
        logger.info("Table or type 'handoffs' already exists; preserving existing structure and data.")
        safe_create_index(bind, "ix_handoffs_project_id", "handoffs", ["project_id"])

def downgrade() -> None:
    bind = op.get_bind()
    # Safe downgrade: drop in reverse dependency order only if relation exists
    for tbl in ["handoffs", "project_versions", "conversations", "context_packages", "projects", "users"]:
        if relation_or_type_exists(bind, tbl):
            op.drop_table(tbl)
