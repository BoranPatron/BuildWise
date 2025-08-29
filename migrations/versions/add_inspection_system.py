"""Add inspection system tables

Revision ID: add_inspection_system
Revises: fix_buildwise_fees_datetime_columns
Create Date: 2025-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_inspection_system'
down_revision = 'fix_buildwise_fees_datetime_columns'  # Referenziere die korrekte letzte Migration
branch_labels = None
depends_on = None


def upgrade():
    """Erstelle Tabellen für das Besichtigungssystem"""
    
    # 1. Erweitere milestones Tabelle um requires_inspection Feld
    op.add_column('milestones', sa.Column('requires_inspection', sa.Boolean(), nullable=True, default=False))
    
    # 2. Erstelle inspections Tabelle
    op.create_table('inspections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('milestone_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'RESCHEDULED', name='inspectionstatus'), nullable=False),
        sa.Column('scheduled_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('location', sa.Text(), nullable=False),
        sa.Column('contact_person', sa.String(), nullable=True),
        sa.Column('contact_phone', sa.String(), nullable=True),
        sa.Column('contact_email', sa.String(), nullable=True),
        sa.Column('special_instructions', sa.Text(), nullable=True),
        sa.Column('required_equipment', sa.Text(), nullable=True),
        sa.Column('inspection_notes', sa.Text(), nullable=True),
        sa.Column('completion_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inspections_id'), 'inspections', ['id'], unique=False)
    
    # 3. Erstelle inspection_invitations Tabelle
    op.create_table('inspection_invitations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('inspection_id', sa.Integer(), nullable=False),
        sa.Column('quote_id', sa.Integer(), nullable=False),
        sa.Column('service_provider_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'ACCEPTED', 'DECLINED', 'EXPIRED', name='inspectioninvitationstatus'), nullable=False),
        sa.Column('response_message', sa.Text(), nullable=True),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notification_sent', sa.Boolean(), nullable=True),
        sa.Column('notification_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reminder_sent', sa.Boolean(), nullable=True),
        sa.Column('reminder_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['inspection_id'], ['inspections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['quote_id'], ['quotes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['service_provider_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inspection_invitations_id'), 'inspection_invitations', ['id'], unique=False)
    
    # 4. Erstelle quote_revisions Tabelle
    op.create_table('quote_revisions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('original_quote_id', sa.Integer(), nullable=False),
        sa.Column('inspection_id', sa.Integer(), nullable=True),
        sa.Column('service_provider_id', sa.Integer(), nullable=False),
        sa.Column('revision_number', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Enum('INSPECTION_FINDINGS', 'SCOPE_CHANGES', 'PRICE_ADJUSTMENT', 'TIMELINE_ADJUSTMENT', 'TECHNICAL_REQUIREMENTS', 'OTHER', name='revisionreason'), nullable=False),
        sa.Column('revision_notes', sa.Text(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('labor_cost', sa.Float(), nullable=True),
        sa.Column('material_cost', sa.Float(), nullable=True),
        sa.Column('overhead_cost', sa.Float(), nullable=True),
        sa.Column('estimated_duration', sa.Integer(), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completion_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('payment_terms', sa.Text(), nullable=True),
        sa.Column('warranty_period', sa.Integer(), nullable=True),
        sa.Column('price_change_amount', sa.Float(), nullable=True),
        sa.Column('price_change_percentage', sa.Float(), nullable=True),
        sa.Column('duration_change_days', sa.Integer(), nullable=True),
        sa.Column('revised_pdf_path', sa.String(), nullable=True),
        sa.Column('additional_documents', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_final', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['inspection_id'], ['inspections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['original_quote_id'], ['quotes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['service_provider_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quote_revisions_id'), 'quote_revisions', ['id'], unique=False)
    
    # 5. Erweitere credit_events Enum um neuen Typ
    op.execute("ALTER TYPE crediteventtype ADD VALUE 'INSPECTION_QUOTE_ACCEPTED'")
    
    # 6. Erstelle Indizes für bessere Performance
    op.create_index('ix_inspections_milestone_id', 'inspections', ['milestone_id'])
    op.create_index('ix_inspections_project_id', 'inspections', ['project_id'])
    op.create_index('ix_inspections_scheduled_date', 'inspections', ['scheduled_date'])
    op.create_index('ix_inspection_invitations_inspection_id', 'inspection_invitations', ['inspection_id'])
    op.create_index('ix_inspection_invitations_quote_id', 'inspection_invitations', ['quote_id'])
    op.create_index('ix_inspection_invitations_service_provider_id', 'inspection_invitations', ['service_provider_id'])
    op.create_index('ix_quote_revisions_original_quote_id', 'quote_revisions', ['original_quote_id'])
    op.create_index('ix_quote_revisions_inspection_id', 'quote_revisions', ['inspection_id'])
    op.create_index('ix_quote_revisions_is_active', 'quote_revisions', ['is_active'])


def downgrade():
    """Entferne Besichtigungssystem-Tabellen"""
    
    # Entferne Indizes
    op.drop_index('ix_quote_revisions_is_active', table_name='quote_revisions')
    op.drop_index('ix_quote_revisions_inspection_id', table_name='quote_revisions')
    op.drop_index('ix_quote_revisions_original_quote_id', table_name='quote_revisions')
    op.drop_index('ix_inspection_invitations_service_provider_id', table_name='inspection_invitations')
    op.drop_index('ix_inspection_invitations_quote_id', table_name='inspection_invitations')
    op.drop_index('ix_inspection_invitations_inspection_id', table_name='inspection_invitations')
    op.drop_index('ix_inspections_scheduled_date', table_name='inspections')
    op.drop_index('ix_inspections_project_id', table_name='inspections')
    op.drop_index('ix_inspections_milestone_id', table_name='inspections')
    
    # Entferne Tabellen
    op.drop_index(op.f('ix_quote_revisions_id'), table_name='quote_revisions')
    op.drop_table('quote_revisions')
    op.drop_index(op.f('ix_inspection_invitations_id'), table_name='inspection_invitations')
    op.drop_table('inspection_invitations')
    op.drop_index(op.f('ix_inspections_id'), table_name='inspections')
    op.drop_table('inspections')
    
    # Entferne Spalte aus milestones
    op.drop_column('milestones', 'requires_inspection')
    
    # Entferne Enums
    op.execute("DROP TYPE IF EXISTS revisionreason")
    op.execute("DROP TYPE IF EXISTS inspectioninvitationstatus")
    op.execute("DROP TYPE IF EXISTS inspectionstatus") 