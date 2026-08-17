"""create users table

Revision ID: a6b4bbe9f5dc
Revises: 7a44fa7565b5
Create Date: 2026-08-17 12:41:26.921243

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a6b4bbe9f5dc'
down_revision = '7a44fa7565b5'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('users', 
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('email', sa.String(), nullable=False),
                    sa.Column('password', sa.String(), nullable=False),
                    sa.Column('created_at', sa.TIMESTAMP(timezone=True),
                               server_default=sa.text('now()'), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('email')    
                    )


def downgrade():
    op.drop_table('users')
    pass
