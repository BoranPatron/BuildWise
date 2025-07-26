"""Add appointments table

Revision ID: add_appointments_table
Revises: 
Create Date: 2025-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_appointments_table'
down_revision = None  # Wird beim Ausführen automatisch gesetzt
branch_labels = None
depends_on = None


def upgrade():
    # Erstelle Enums
    appointment_type_enum = postgresql.ENUM(
        'inspection', 'meeting', 'consultation', 'review',
        name='appointmenttype'
    )
    appointment_type_enum.create(op.get_bind())
    
    appointment_status_enum = postgresql.ENUM(
        'scheduled', 'confirmed', 'pending_response', 'accepted', 
        'rejected', 'rejected_with_suggestion', 'completed', 'cancelled',
        name='appointmentstatus'
    )
    appointment_status_enum.create(op.get_bind())
    
    # Erstelle appointments Tabelle
    op.create_table(
        'appointments',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True, index=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('milestone_id', sa.Integer(), sa.ForeignKey('milestones.id'), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        
        # Termin-Details
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('appointment_type', appointment_type_enum, nullable=False, default='inspection'),
        sa.Column('status', appointment_status_enum, nullable=False, default='scheduled'),
        
        # Zeitplanung
        sa.Column('scheduled_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, default=60),
        
        # Teilnehmer und Antworten (JSON)
        sa.Column('invited_service_providers', sa.JSON(), nullable=True),
        sa.Column('responses', sa.JSON(), nullable=True),
        
        # Ort
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('location_details', sa.Text(), nullable=True),
        
        # Ergebnis der Besichtigung
        sa.Column('inspection_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('selected_service_provider_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('inspection_notes', sa.Text(), nullable=True),
        sa.Column('inspection_photos', sa.JSON(), nullable=True),
        
        # Nachverhandlung
        sa.Column('requires_renegotiation', sa.Boolean(), nullable=False, default=False),
        sa.Column('renegotiation_details', sa.Text(), nullable=True),
        
        # Kalender-Download
        sa.Column('calendar_event_data', sa.JSON(), nullable=True),
        
        # Benachrichtigungen
        sa.Column('notification_sent', sa.Boolean(), nullable=False, default=False),
        sa.Column('follow_up_notification_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('follow_up_sent', sa.Boolean(), nullable=False, default=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Erstelle Indizes
    op.create_index('ix_appointments_project_id', 'appointments', ['project_id'])
    op.create_index('ix_appointments_milestone_id', 'appointments', ['milestone_id'])
    op.create_index('ix_appointments_created_by', 'appointments', ['created_by'])
    op.create_index('ix_appointments_status', 'appointments', ['status'])
    op.create_index('ix_appointments_scheduled_date', 'appointments', ['scheduled_date'])
    op.create_index('ix_appointments_follow_up', 'appointments', ['follow_up_notification_date', 'follow_up_sent'])


def downgrade():
    # Lösche Tabelle und Indizes
    op.drop_index('ix_appointments_follow_up', 'appointments')
    op.drop_index('ix_appointments_scheduled_date', 'appointments')
    op.drop_index('ix_appointments_status', 'appointments')
    op.drop_index('ix_appointments_created_by', 'appointments')
    op.drop_index('ix_appointments_milestone_id', 'appointments')
    op.drop_index('ix_appointments_project_id', 'appointments')
    
    op.drop_table('appointments')
    
    # Lösche Enums
    op.execute('DROP TYPE appointmentstatus')
    op.execute('DROP TYPE appointmenttype') 