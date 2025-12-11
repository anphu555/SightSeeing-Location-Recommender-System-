"""add_bio_location_to_user

Revision ID: 6190953e9c16
Revises: 1a680e75d0a0
Create Date: 2025-12-11 15:44:52.365011

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '6190953e9c16'
down_revision: Union[str, Sequence[str], None] = '1a680e75d0a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add bio column (nullable, text field)
    op.add_column('user', sa.Column('bio', sa.String(), nullable=True))
    
    # Add location column (nullable)
    op.add_column('user', sa.Column('location', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove location column
    op.drop_column('user', 'location')
    
    # Remove bio column
    op.drop_column('user', 'bio')
