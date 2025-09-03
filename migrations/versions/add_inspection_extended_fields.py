"""Add extended fields to inspection system

Revision ID: add_inspection_extended_fields
Revises: add_inspection_system
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_inspection_extended_fields'
down_revision = 'add_inspection_system'
branch_labels = None
depends_on = None


def upgrade():
    # Erweitere die inspections Tabelle um die neuen Felder
    op.add_column('inspections', sa.Column('additional_location_info', sa.Text(), nullable=True))
    op.add_column('inspections', sa.Column('parking_info', sa.String(), nullable=True))
    op.add_column('inspections', sa.Column('access_instructions', sa.Text(), nullable=True))
    op.add_column('inspections', sa.Column('contact_email', sa.String(), nullable=True))
    op.add_column('inspections', sa.Column('alternative_contact_person', sa.String(), nullable=True))
    op.add_column('inspections', sa.Column('alternative_contact_phone', sa.String(), nullable=True))
    op.add_column('inspections', sa.Column('special_requirements', sa.Text(), nullable=True))
    
    # Benenne bestehende Spalten um, falls sie existieren
    try:
        op.alter_column('inspections', 'location', new_column_name='location_address')
    except:
        # Falls die Spalte nicht existiert, erstelle sie
        op.add_column('inspections', sa.Column('location_address', sa.String(), nullable=True))


def downgrade():
    # Entferne die neuen Spalten
    op.drop_column('inspections', 'special_requirements')
    op.drop_column('inspections', 'alternative_contact_phone')
    op.drop_column('inspections', 'alternative_contact_person')
    op.drop_column('inspections', 'contact_email')
    op.drop_column('inspections', 'access_instructions')
    op.drop_column('inspections', 'parking_info')
    op.drop_column('inspections', 'additional_location_info')
    
    # Benenne location_address zurück zu location
    try:
        op.alter_column('inspections', 'location_address', new_column_name='location')
    except:
        pass
