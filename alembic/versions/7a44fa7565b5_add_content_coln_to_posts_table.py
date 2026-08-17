"""add content coln to posts table

Revision ID: 7a44fa7565b5
Revises: 54367880dde6
Create Date: 2026-08-17 12:13:13.568244

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a44fa7565b5'
down_revision = '54367880dde6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('posts', sa.Column("content", sa.String(), nullable=False))


def downgrade():
    op.drop_column('posts', 'content')
