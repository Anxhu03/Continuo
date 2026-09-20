"""context images

Revision ID: 0003_context_images
Revises: 0002_context_os_entities
Create Date: 2026-09-21 00:00:00.000000

"""
from typing import Sequence, Union
import logging
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

# revision identifiers, used by Alembic.
revision: str = '0003_context_images'
down_revision: Union[str, None] = '0002_context_os_entities'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger("alembic.runtime.migration")


def relation_or_type_exists(bind, name: str) -> bool:
    """Check if table, view, composite type, or enum relation exists in the database."""
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


def safe_create_index(index_name: str, table_name: str, columns: list, unique: bool = False):
    """Safely create index only if it does not already exist."""
    bind = op.get_bind()
    inspector = inspect(bind)
    try:
        existing_indices = [idx["name"] for idx in inspector.get_indexes(table_name)]
        if index_name not in existing_indices:
            op.create_index(index_name, table_name, columns, unique=unique)
    except Exception as e:
        logger.warning(f"Index check/create warning for {index_name}: {e}")
        try:
            op.create_index(index_name, table_name, columns, unique=unique)
        except Exception:
            pass


def upgrade() -> None:
    bind = op.get_bind()

    if not relation_or_type_exists(bind, "context_images"):
        op.create_table(
            'context_images',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('project_id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=False),
            sa.Column('original_filename', sa.String(length=255), nullable=False),
            sa.Column('storage_key', sa.String(length=512), nullable=False),
            sa.Column('mime_type', sa.String(length=64), nullable=False),
            sa.Column('image_format', sa.String(length=32), nullable=False),
            sa.Column('file_size', sa.Integer(), nullable=False),
            sa.Column('width', sa.Integer(), nullable=True),
            sa.Column('height', sa.Integer(), nullable=True),
            sa.Column('checksum_sha256', sa.String(length=64), nullable=False),
            sa.Column('image_type', sa.String(length=64), server_default='other', nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('visual_tags_json', sa.Text(), server_default='[]', nullable=False),
            sa.Column('associated_context_ids_json', sa.Text(), server_default='[]', nullable=False),
            sa.Column('associated_decision_ids_json', sa.Text(), server_default='[]', nullable=False),
            sa.Column('associated_session_id', sa.String(length=36), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['associated_session_id'], ['conversations.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('storage_key', name='uq_context_images_storage_key')
        )

    safe_create_index('ix_context_images_project_id', 'context_images', ['project_id'])
    safe_create_index('ix_context_images_user_id', 'context_images', ['user_id'])
    safe_create_index('ix_context_images_storage_key', 'context_images', ['storage_key'], unique=True)
    safe_create_index('ix_context_images_checksum_sha256', 'context_images', ['checksum_sha256'])
    safe_create_index('ix_context_images_associated_session_id', 'context_images', ['associated_session_id'])
    safe_create_index('ix_context_images_proj_type', 'context_images', ['project_id', 'image_type'])


def downgrade() -> None:
    bind = op.get_bind()
    if relation_or_type_exists(bind, "context_images"):
        op.drop_table('context_images')
