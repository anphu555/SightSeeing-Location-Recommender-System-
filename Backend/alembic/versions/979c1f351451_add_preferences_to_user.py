"""add_preferences_to_user

Revision ID: 979c1f351451
Revises: 63b78bb02380
Create Date: 2025-12-07 22:12:36.604434

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '979c1f351451'
down_revision: Union[str, Sequence[str], None] = '63b78bb02380'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add preferences column as JSON to user table with default empty array
    op.add_column('user', sa.Column('preferences', sa.JSON(), nullable=False, server_default='[]'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove preferences column from user table
    op.drop_column('user', 'preferences')
