"""add owner id fkey to posts table

Revision ID: 82f44b04f993
Revises: a6b4bbe9f5dc
Create Date: 2026-08-17 13:19:04.242101

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '82f44b04f993'
down_revision = 'a6b4bbe9f5dc'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('posts', sa.Column('owner_id', sa.Integer(), nullable=False))
    op.create_foreign_key('fk_posts_owner_id_users', source_table='posts', referent_table='users',
                          local_cols=['owner_id'], remote_cols=['id'], ondelete='CASCADE')


def downgrade():
    op.drop_constraint('fk_posts_owner_id_users', table_name='posts')
    op.drop_column('posts', 'owner_id')
