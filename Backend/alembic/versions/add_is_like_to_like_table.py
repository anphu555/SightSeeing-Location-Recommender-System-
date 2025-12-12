"""add is_like to like table

Revision ID: add_is_like_field
Revises: 2103b65d3fb9
Create Date: 2025-12-12

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_is_like_field'
down_revision = '2103b65d3fb9'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_like column (True=like, False=dislike, None=neutral/removed)
    # Default True để các like cũ vẫn là like
    with op.batch_alter_table('like', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_like', sa.Boolean(), nullable=True, server_default='1'))
    
    # Update existing records to True (convert old likes to new like format)
    op.execute("UPDATE like SET is_like = 1")


def downgrade():
    with op.batch_alter_table('like', schema=None) as batch_op:
        batch_op.drop_column('is_like')
