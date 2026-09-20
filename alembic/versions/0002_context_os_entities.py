"""context os entities

Revision ID: 0002_context_os_entities
Revises: 0001_initial_schema
Create Date: 2026-09-20 23:30:00.000000

"""
from typing import Sequence, Union
import logging
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

# revision identifiers, used by Alembic.
revision: str = '0002_context_os_entities'
down_revision: Union[str, None] = '0001_initial_schema'
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

    # 1. context_goals table
    if not relation_or_type_exists(bind, "context_goals"):
        op.create_table(
            "context_goals",
            sa.Column("id", sa.String(36), primary_key=True, nullable=False),
            sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("category", sa.String(64), nullable=False, server_default="goal"),
            sa.Column("status", sa.String(32), nullable=False, server_default="active"),
            sa.Column("priority", sa.String(32), nullable=False, server_default="normal"),
            sa.Column("source_session_id", sa.String(36), sa.ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        safe_create_index(bind, "ix_context_goals_project_id", "context_goals", ["project_id"])
        safe_create_index(bind, "ix_context_goals_user_id", "context_goals", ["user_id"])
        safe_create_index(bind, "ix_context_goals_project_status", "context_goals", ["project_id", "status"])
        safe_create_index(bind, "ix_context_goals_project_updated", "context_goals", ["project_id", "updated_at"])
        logger.info("Created table: context_goals")
    else:
        logger.info("Table or type 'context_goals' already exists; preserving existing structure.")
        safe_create_index(bind, "ix_context_goals_project_id", "context_goals", ["project_id"])
        safe_create_index(bind, "ix_context_goals_user_id", "context_goals", ["user_id"])
        safe_create_index(bind, "ix_context_goals_project_status", "context_goals", ["project_id", "status"])
        safe_create_index(bind, "ix_context_goals_project_updated", "context_goals", ["project_id", "updated_at"])

    # 2. context_decisions table
    if not relation_or_type_exists(bind, "context_decisions"):
        op.create_table(
            "context_decisions",
            sa.Column("id", sa.String(36), primary_key=True, nullable=False),
            sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("rationale", sa.Text(), nullable=True),
            sa.Column("category", sa.String(64), nullable=False, server_default="architecture"),
            sa.Column("status", sa.String(32), nullable=False, server_default="accepted"),
            sa.Column("source_session_id", sa.String(36), sa.ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True),
            sa.Column("superseded_by_id", sa.String(36), sa.ForeignKey("context_decisions.id", ondelete="SET NULL"), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        safe_create_index(bind, "ix_context_decisions_project_id", "context_decisions", ["project_id"])
        safe_create_index(bind, "ix_context_decisions_user_id", "context_decisions", ["user_id"])
        safe_create_index(bind, "ix_context_decisions_project_status", "context_decisions", ["project_id", "status"])
        safe_create_index(bind, "ix_context_decisions_project_updated", "context_decisions", ["project_id", "updated_at"])
        safe_create_index(bind, "ix_context_decisions_superseded_by", "context_decisions", ["superseded_by_id"])
        logger.info("Created table: context_decisions")
    else:
        logger.info("Table or type 'context_decisions' already exists; preserving existing structure.")
        safe_create_index(bind, "ix_context_decisions_project_id", "context_decisions", ["project_id"])
        safe_create_index(bind, "ix_context_decisions_user_id", "context_decisions", ["user_id"])
        safe_create_index(bind, "ix_context_decisions_project_status", "context_decisions", ["project_id", "status"])
        safe_create_index(bind, "ix_context_decisions_project_updated", "context_decisions", ["project_id", "updated_at"])
        safe_create_index(bind, "ix_context_decisions_superseded_by", "context_decisions", ["superseded_by_id"])

    # 3. context_tasks table
    if not relation_or_type_exists(bind, "context_tasks"):
        op.create_table(
            "context_tasks",
            sa.Column("id", sa.String(36), primary_key=True, nullable=False),
            sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="todo"),
            sa.Column("priority", sa.String(32), nullable=False, server_default="normal"),
            sa.Column("source_session_id", sa.String(36), sa.ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        safe_create_index(bind, "ix_context_tasks_project_id", "context_tasks", ["project_id"])
        safe_create_index(bind, "ix_context_tasks_user_id", "context_tasks", ["user_id"])
        safe_create_index(bind, "ix_context_tasks_project_status", "context_tasks", ["project_id", "status"])
        safe_create_index(bind, "ix_context_tasks_project_updated", "context_tasks", ["project_id", "updated_at"])
        logger.info("Created table: context_tasks")
    else:
        logger.info("Table or type 'context_tasks' already exists; preserving existing structure.")
        safe_create_index(bind, "ix_context_tasks_project_id", "context_tasks", ["project_id"])
        safe_create_index(bind, "ix_context_tasks_user_id", "context_tasks", ["user_id"])
        safe_create_index(bind, "ix_context_tasks_project_status", "context_tasks", ["project_id", "status"])
        safe_create_index(bind, "ix_context_tasks_project_updated", "context_tasks", ["project_id", "updated_at"])

    # 4. context_technical_states table
    if not relation_or_type_exists(bind, "context_technical_states"):
        op.create_table(
            "context_technical_states",
            sa.Column("id", sa.String(36), primary_key=True, nullable=False),
            sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("category", sa.String(64), nullable=False),
            sa.Column("key", sa.String(128), nullable=False),
            sa.Column("value", sa.Text(), nullable=False),
            sa.Column("source_session_id", sa.String(36), sa.ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.UniqueConstraint("project_id", "category", "key", name="uq_tech_state_project_cat_key"),
        )
        safe_create_index(bind, "ix_context_technical_states_project_id", "context_technical_states", ["project_id"])
        safe_create_index(bind, "ix_context_technical_states_user_id", "context_technical_states", ["user_id"])
        safe_create_index(bind, "ix_context_technical_states_project_cat", "context_technical_states", ["project_id", "category"])
        safe_create_index(bind, "ix_context_technical_states_project_updated", "context_technical_states", ["project_id", "updated_at"])
        logger.info("Created table: context_technical_states")
    else:
        logger.info("Table or type 'context_technical_states' already exists; preserving existing structure.")
        safe_create_index(bind, "ix_context_technical_states_project_id", "context_technical_states", ["project_id"])
        safe_create_index(bind, "ix_context_technical_states_user_id", "context_technical_states", ["user_id"])
        safe_create_index(bind, "ix_context_technical_states_project_cat", "context_technical_states", ["project_id", "category"])
        safe_create_index(bind, "ix_context_technical_states_project_updated", "context_technical_states", ["project_id", "updated_at"])

def downgrade() -> None:
    bind = op.get_bind()
    # Safe downgrade: drop in reverse dependency order only if relation exists
    for tbl in [
        "context_technical_states",
        "context_tasks",
        "context_decisions",
        "context_goals",
    ]:
        if relation_or_type_exists(bind, tbl):
            op.drop_table(tbl)
            logger.info(f"Dropped table: {tbl}")
