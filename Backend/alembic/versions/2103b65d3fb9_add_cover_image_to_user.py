"""add_cover_image_to_user

Revision ID: 2103b65d3fb9
Revises: 6190953e9c16
Create Date: 2025-12-11 16:23:58.890228

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '2103b65d3fb9'
down_revision: Union[str, Sequence[str], None] = '6190953e9c16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add cover_image_url column (nullable)
    op.add_column('user', sa.Column('cover_image_url', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove cover_image_url column
    op.drop_column('user', 'cover_image_url')
