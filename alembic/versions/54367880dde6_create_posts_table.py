"""create posts table

Revision ID: 54367880dde6
Revises: 
Create Date: 2026-08-17 11:57:41.996797

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '54367880dde6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('posts', 
                    sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
                    sa.Column('title', sa.String(), nullable=False))
    


def downgrade():
    op.drop_table('posts')
    
