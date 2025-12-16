"""Add climate and coordinates to place table

Revision ID: add_climate_coords
Revises: 2103b65d3fb9
Create Date: 2024-12-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_climate_coords'
down_revision: Union[str, None] = 'add_is_like_field'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add latitude column
    op.add_column('place', sa.Column('lat', sa.Float(), nullable=True))
    # Add longitude column
    op.add_column('place', sa.Column('lon', sa.Float(), nullable=True))
    # Add climate column (e.g., "cool", "warm", "hot", "cold")
    op.add_column('place', sa.Column('climate', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('place', 'lat')
    op.drop_column('place', 'lon')
    op.drop_column('place', 'climate')
