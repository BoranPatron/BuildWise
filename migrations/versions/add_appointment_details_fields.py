"""Add appointment details fields

Revision ID: add_appointment_details_fields
Revises: add_inspection_system
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_appointment_details_fields'
down_revision = 'add_inspection_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add contact_person, contact_phone, and preparation_notes fields to appointments table"""
    # Add new columns to appointments table
    op.add_column('appointments', sa.Column('contact_person', sa.String(), nullable=True))
    op.add_column('appointments', sa.Column('contact_phone', sa.String(), nullable=True))
    op.add_column('appointments', sa.Column('preparation_notes', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove appointment details fields"""
    op.drop_column('appointments', 'preparation_notes')
    op.drop_column('appointments', 'contact_phone')
    op.drop_column('appointments', 'contact_person')
