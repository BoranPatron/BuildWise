"""Add gamification fields to users table

Revision ID: add_gamification_fields
Revises: add_last_daily_deduction
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_gamification_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add gamification fields to users table
    op.add_column('users', sa.Column('current_rank_key', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('current_rank_title', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('rank_updated_at', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    # Remove gamification fields from users table
    op.drop_column('users', 'rank_updated_at')
    op.drop_column('users', 'current_rank_title')
    op.drop_column('users', 'current_rank_key')
