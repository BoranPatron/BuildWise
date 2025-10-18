"""Add last_daily_deduction field to user_credits

Revision ID: add_last_daily_deduction
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_last_daily_deduction'
down_revision = 'add_gamification_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Add last_daily_deduction column to user_credits table
    op.add_column('user_credits', sa.Column('last_daily_deduction', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    # Remove last_daily_deduction column from user_credits table
    op.drop_column('user_credits', 'last_daily_deduction')
