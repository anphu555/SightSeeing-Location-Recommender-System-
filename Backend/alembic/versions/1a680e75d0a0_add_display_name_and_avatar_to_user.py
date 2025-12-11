"""add_display_name_and_avatar_to_user

Revision ID: 1a680e75d0a0
Revises: 979c1f351451
Create Date: 2025-12-11 14:57:38.553919

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '1a680e75d0a0'
down_revision: Union[str, Sequence[str], None] = '979c1f351451'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add display_name column (nullable, defaults to username if not set)
    op.add_column('user', sa.Column('display_name', sa.String(), nullable=True))
    
    # Add avatar_url column (nullable, defaults to None for default avatar)
    op.add_column('user', sa.Column('avatar_url', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove avatar_url column
    op.drop_column('user', 'avatar_url')
    
    # Remove display_name column
    op.drop_column('user', 'display_name')
