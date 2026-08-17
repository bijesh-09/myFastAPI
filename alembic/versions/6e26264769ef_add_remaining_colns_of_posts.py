"""add remaining colns of posts

Revision ID: 6e26264769ef
Revises: 82f44b04f993
Create Date: 2026-08-17 13:27:57.849217

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6e26264769ef'
down_revision = '82f44b04f993'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('posts', sa.Column("published", sa.Boolean(), nullable=False, server_default='TRUE'))
    op.add_column('posts', sa.Column("created_at", sa.TIMESTAMP(timezone=True), 
                                      server_default=sa.text('now()'), nullable=False))

def downgrade():
    op.drop_column('posts', 'published')
    op.drop_column('posts', 'created_at')
