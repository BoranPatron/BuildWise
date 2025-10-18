"""Merge multiple heads

Revision ID: 670708bfcd4a
Revises: add_appointment_details_fields, add_appointments_table, add_construction_phase_columns, add_construction_phase_to_milestones, add_inspection_extended_fields, add_last_daily_deduction
Create Date: 2025-10-18 16:54:02.103043

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '670708bfcd4a'
down_revision = ('add_appointment_details_fields', 'add_appointments_table', 'add_construction_phase_columns', 'add_construction_phase_to_milestones', 'add_inspection_extended_fields', 'add_last_daily_deduction')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

