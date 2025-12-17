"""Add forum tables (Post, PostLike, PostComment)

Revision ID: add_forum_tables
Revises: 2103b65d3fb9
Create Date: 2025-12-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'add_forum_tables'
down_revision: Union[str, None] = '2103b65d3fb9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create Post table
    op.create_table(
        'post',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('place_id', sa.Integer(), nullable=True),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('images', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('like_count', sa.Integer(), default=0),
        sa.Column('comment_count', sa.Integer(), default=0),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['place_id'], ['place.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_post_user_id'), 'post', ['user_id'], unique=False)
    op.create_index(op.f('ix_post_created_at'), 'post', ['created_at'], unique=False)

    # Create PostLike table
    op.create_table(
        'postlike',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['post_id'], ['post.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # Unique constraint để 1 user chỉ like 1 post 1 lần
    op.create_index('ix_postlike_user_post', 'postlike', ['user_id', 'post_id'], unique=True)

    # Create PostComment table
    op.create_table(
        'postcomment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['post_id'], ['post.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_postcomment_post_id'), 'postcomment', ['post_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_postcomment_post_id'), table_name='postcomment')
    op.drop_table('postcomment')
    op.drop_index('ix_postlike_user_post', table_name='postlike')
    op.drop_table('postlike')
    op.drop_index(op.f('ix_post_created_at'), table_name='post')
    op.drop_index(op.f('ix_post_user_id'), table_name='post')
    op.drop_table('post')
