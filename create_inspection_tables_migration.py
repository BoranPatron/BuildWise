"""create inspection tables

Revision ID: create_inspection_tables
Revises: 
Create Date: 2025-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_inspection_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create InspectionStatus enum
    inspection_status_enum = sa.Enum(
        'PLANNED', 'INVITED', 'CONFIRMED', 'COMPLETED', 'CANCELLED',
        name='inspectionstatus'
    )
    inspection_status_enum.create(op.get_bind())
    
    # Create InspectionInvitationStatus enum
    invitation_status_enum = sa.Enum(
        'SENT', 'CONFIRMED', 'DECLINED', 'NO_RESPONSE',
        name='inspectioninvitationstatus'
    )
    invitation_status_enum.create(op.get_bind())
    
    # Create inspections table
    op.create_table('inspections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('milestone_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', inspection_status_enum, nullable=True),
        sa.Column('scheduled_date', sa.Date(), nullable=False),
        sa.Column('scheduled_time_start', sa.String(), nullable=True),
        sa.Column('scheduled_time_end', sa.String(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('location_address', sa.String(), nullable=True),
        sa.Column('location_notes', sa.Text(), nullable=True),
        sa.Column('contact_person', sa.String(), nullable=True),
        sa.Column('contact_phone', sa.String(), nullable=True),
        sa.Column('preparation_notes', sa.Text(), nullable=True),
        sa.Column('completion_notes', sa.Text(), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inspections_id'), 'inspections', ['id'], unique=False)
    
    # Create inspection_invitations table
    op.create_table('inspection_invitations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('inspection_id', sa.Integer(), nullable=True),
        sa.Column('service_provider_id', sa.Integer(), nullable=True),
        sa.Column('quote_id', sa.Integer(), nullable=True),
        sa.Column('status', invitation_status_enum, nullable=True),
        sa.Column('response_message', sa.Text(), nullable=True),
        sa.Column('alternative_dates', sa.Text(), nullable=True),
        sa.Column('notification_sent', sa.Boolean(), nullable=True),
        sa.Column('notification_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reminder_sent', sa.Boolean(), nullable=True),
        sa.Column('reminder_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['inspection_id'], ['inspections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['service_provider_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['quote_id'], ['quotes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inspection_invitations_id'), 'inspection_invitations', ['id'], unique=False)
    
    # Create quote_revisions table
    op.create_table('quote_revisions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('original_quote_id', sa.Integer(), nullable=True),
        sa.Column('inspection_id', sa.Integer(), nullable=True),
        sa.Column('service_provider_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('revision_reason', sa.Text(), nullable=True),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.Column('labor_cost', sa.Float(), nullable=True),
        sa.Column('material_cost', sa.Float(), nullable=True),
        sa.Column('overhead_cost', sa.Float(), nullable=True),
        sa.Column('amount_difference', sa.Float(), nullable=True),
        sa.Column('amount_difference_percentage', sa.Float(), nullable=True),
        sa.Column('estimated_duration', sa.Integer(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('completion_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('confirmed_by_client', sa.Boolean(), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejected_by', sa.Integer(), nullable=True),
        sa.Column('pdf_upload_path', sa.String(), nullable=True),
        sa.Column('additional_documents', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['inspection_id'], ['inspections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['original_quote_id'], ['quotes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['rejected_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['service_provider_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quote_revisions_id'), 'quote_revisions', ['id'], unique=False)


def downgrade():
    # Drop tables
    op.drop_index(op.f('ix_quote_revisions_id'), table_name='quote_revisions')
    op.drop_table('quote_revisions')
    
    op.drop_index(op.f('ix_inspection_invitations_id'), table_name='inspection_invitations')
    op.drop_table('inspection_invitations')
    
    op.drop_index(op.f('ix_inspections_id'), table_name='inspections')
    op.drop_table('inspections')
    
    # Drop enums
    sa.Enum(name='inspectioninvitationstatus').drop(op.get_bind())
    sa.Enum(name='inspectionstatus').drop(op.get_bind()) 