"""Initial complete schema migration

Revision ID: 00_initial_complete_schema
Revises: 
Create Date: 2025-10-22 07:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '00_initial_complete_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM types
    op.execute("CREATE TYPE usertype AS ENUM ('contractor', 'service_provider')")
    op.execute("CREATE TYPE userstatus AS ENUM ('active', 'inactive', 'suspended', 'pending_verification')")
    op.execute("CREATE TYPE userrole AS ENUM ('admin', 'user', 'moderator')")
    op.execute("CREATE TYPE authprovider AS ENUM ('local', 'google', 'microsoft', 'apple')")
    op.execute("CREATE TYPE projecttype AS ENUM ('residential', 'commercial', 'industrial', 'renovation')")
    op.execute("CREATE TYPE projectstatus AS ENUM ('planning', 'active', 'completed', 'cancelled', 'on_hold')")
    op.execute("CREATE TYPE taskstatus AS ENUM ('pending', 'in_progress', 'completed', 'cancelled')")
    op.execute("CREATE TYPE taskpriority AS ENUM ('low', 'medium', 'high', 'urgent')")
    op.execute("CREATE TYPE documenttype AS ENUM ('plan', 'contract', 'invoice', 'photo', 'report', 'other')")
    op.execute("CREATE TYPE documentcategory AS ENUM ('architectural', 'structural', 'electrical', 'plumbing', 'hvac', 'other')")
    op.execute("CREATE TYPE documentstatus AS ENUM ('draft', 'pending_review', 'approved', 'rejected', 'archived')")
    op.execute("CREATE TYPE workflowstage AS ENUM ('draft', 'review', 'approval', 'published', 'archived')")
    op.execute("CREATE TYPE approvalstatus AS ENUM ('pending', 'approved', 'rejected', 'requires_changes')")
    op.execute("CREATE TYPE reviewstatus AS ENUM ('not_reviewed', 'in_review', 'reviewed', 'requires_revision')")
    op.execute("CREATE TYPE sharetype AS ENUM ('public', 'private', 'restricted', 'temporary')")
    op.execute("CREATE TYPE accesslevel AS ENUM ('read', 'write', 'admin', 'owner')")
    op.execute("CREATE TYPE changetype AS ENUM ('create', 'update', 'delete', 'restore')")
    op.execute("CREATE TYPE milestonestatus AS ENUM ('pending', 'in_progress', 'completed', 'cancelled', 'on_hold')")
    op.execute("CREATE TYPE milestonepriority AS ENUM ('low', 'medium', 'high', 'critical')")
    op.execute("CREATE TYPE quotestatus AS ENUM ('draft', 'submitted', 'accepted', 'rejected', 'expired')")
    op.execute("CREATE TYPE messagetype AS ENUM ('text', 'file', 'system', 'notification')")
    op.execute("CREATE TYPE auditaction AS ENUM ('create', 'read', 'update', 'delete', 'login', 'logout', 'export', 'import')")
    op.execute("CREATE TYPE planstatus AS ENUM ('free', 'pro', 'premium')")
    op.execute("CREATE TYPE crediteventtype AS ENUM ('purchase', 'deduction', 'bonus', 'refund', 'expiration')")
    op.execute("CREATE TYPE purchasestatus AS ENUM ('pending', 'completed', 'failed', 'refunded')")
    op.execute("CREATE TYPE inspectionstatus AS ENUM ('scheduled', 'in_progress', 'completed', 'cancelled')")
    op.execute("CREATE TYPE inspectioninvitationstatus AS ENUM ('sent', 'accepted', 'declined', 'expired')")
    op.execute("CREATE TYPE appointmenttype AS ENUM ('inspection', 'meeting', 'delivery', 'maintenance')")
    op.execute("CREATE TYPE appointmentstatus AS ENUM ('scheduled', 'confirmed', 'in_progress', 'completed', 'cancelled', 'rescheduled')")
    op.execute("CREATE TYPE acceptancestatus AS ENUM ('pending', 'in_progress', 'accepted', 'rejected', 'requires_revision')")
    op.execute("CREATE TYPE acceptancetype AS ENUM ('quality', 'completion', 'final', 'partial')")
    op.execute("CREATE TYPE defectseverity AS ENUM ('minor', 'major', 'critical')")
    op.execute("CREATE TYPE invoicestatus AS ENUM ('draft', 'sent', 'paid', 'overdue', 'cancelled')")
    op.execute("CREATE TYPE invoicetype AS ENUM ('invoice', 'credit')")
    op.execute("CREATE TYPE progressupdatetype AS ENUM ('manual', 'automatic', 'photo', 'document')")
    op.execute("CREATE TYPE visualizationcategory AS ENUM ('3d_model', 'rendering', 'animation', 'vr')")
    op.execute("CREATE TYPE visualizationstatus AS ENUM ('pending', 'processing', 'completed', 'failed')")
    op.execute("CREATE TYPE notificationtype AS ENUM ('info', 'warning', 'error', 'success', 'reminder')")
    op.execute("CREATE TYPE notificationpriority AS ENUM ('low', 'medium', 'high', 'urgent')")
    op.execute("CREATE TYPE resourcestatus AS ENUM ('available', 'allocated', 'busy', 'unavailable')")
    op.execute("CREATE TYPE resourcevisibility AS ENUM ('public', 'private', 'restricted')")
    op.execute("CREATE TYPE allocationstatus AS ENUM ('pending', 'confirmed', 'active', 'completed', 'cancelled')")
    op.execute("CREATE TYPE requeststatus AS ENUM ('open', 'in_progress', 'fulfilled', 'cancelled', 'expired')")
    op.execute("CREATE TYPE calendarentrystatus AS ENUM ('tentative', 'confirmed', 'cancelled')")

    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=True),
        sa.Column('auth_provider', sa.Enum('local', 'google', 'microsoft', 'apple', name='authprovider'), nullable=False),
        sa.Column('google_sub', sa.String(), nullable=True),
        sa.Column('microsoft_sub', sa.String(), nullable=True),
        sa.Column('apple_sub', sa.String(), nullable=True),
        sa.Column('social_profile_data', sa.JSON(), nullable=True),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('user_type', sa.Enum('contractor', 'service_provider', name='usertype'), nullable=False),
        sa.Column('user_role', sa.Enum('admin', 'user', 'moderator', name='userrole'), nullable=True),
        sa.Column('role_selected', sa.Boolean(), nullable=True),
        sa.Column('role_selected_at', sa.DateTime(), nullable=True),
        sa.Column('role_selection_modal_shown', sa.Boolean(), nullable=True),
        sa.Column('first_login_completed', sa.Boolean(), nullable=True),
        sa.Column('onboarding_completed', sa.Boolean(), nullable=True),
        sa.Column('onboarding_step', sa.Integer(), nullable=True),
        sa.Column('onboarding_started_at', sa.DateTime(), nullable=True),
        sa.Column('onboarding_completed_at', sa.DateTime(), nullable=True),
        sa.Column('subscription_plan', sa.String(length=5), nullable=True),
        sa.Column('subscription_status', sa.String(length=8), nullable=True),
        sa.Column('subscription_id', sa.String(), nullable=True),
        sa.Column('customer_id', sa.String(), nullable=True),
        sa.Column('subscription_start', sa.DateTime(), nullable=True),
        sa.Column('subscription_end', sa.DateTime(), nullable=True),
        sa.Column('max_gewerke', sa.Integer(), nullable=True),
        sa.Column('address_street', sa.String(), nullable=True),
        sa.Column('address_zip', sa.String(), nullable=True),
        sa.Column('address_city', sa.String(), nullable=True),
        sa.Column('address_country', sa.String(), nullable=True),
        sa.Column('address_latitude', sa.Float(), nullable=True),
        sa.Column('address_longitude', sa.Float(), nullable=True),
        sa.Column('address_geocoded', sa.Boolean(), nullable=True),
        sa.Column('address_geocoding_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.Enum('active', 'inactive', 'suspended', 'pending_verification', name='userstatus'), nullable=False),
        sa.Column('consent_fields', sa.JSON(), nullable=True),
        sa.Column('consent_history', sa.JSON(), nullable=True),
        sa.Column('data_processing_consent', sa.Boolean(), nullable=True),
        sa.Column('marketing_consent', sa.Boolean(), nullable=True),
        sa.Column('privacy_policy_accepted', sa.Boolean(), nullable=True),
        sa.Column('terms_accepted', sa.Boolean(), nullable=True),
        sa.Column('data_retention_until', sa.Date(), nullable=True),
        sa.Column('data_deletion_requested', sa.Boolean(), nullable=True),
        sa.Column('data_deletion_requested_at', sa.DateTime(), nullable=True),
        sa.Column('data_anonymized', sa.Boolean(), nullable=True),
        sa.Column('data_export_requested', sa.Boolean(), nullable=True),
        sa.Column('data_export_requested_at', sa.DateTime(), nullable=True),
        sa.Column('data_export_token', sa.String(), nullable=True),
        sa.Column('data_export_expires_at', sa.DateTime(), nullable=True),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('last_login_provider', sa.Enum('local', 'google', 'microsoft', 'apple', name='authprovider'), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=True),
        sa.Column('account_locked_until', sa.DateTime(), nullable=True),
        sa.Column('password_changed_at', sa.DateTime(), nullable=True),
        sa.Column('mfa_enabled', sa.Boolean(), nullable=True),
        sa.Column('mfa_secret', sa.String(), nullable=True),
        sa.Column('mfa_backup_codes', sa.JSON(), nullable=True),
        sa.Column('mfa_last_used', sa.DateTime(), nullable=True),
        sa.Column('company_name', sa.String(), nullable=True),
        sa.Column('company_address', sa.Text(), nullable=True),
        sa.Column('company_uid', sa.String(length=50), nullable=True),
        sa.Column('company_tax_number', sa.String(length=50), nullable=True),
        sa.Column('company_phone', sa.String(), nullable=True),
        sa.Column('company_website', sa.String(), nullable=True),
        sa.Column('business_license', sa.String(), nullable=True),
        sa.Column('is_small_business', sa.Boolean(), nullable=True),
        sa.Column('small_business_exemption', sa.Boolean(), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('profile_image', sa.String(), nullable=True),
        sa.Column('region', sa.String(), nullable=True),
        sa.Column('languages', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('email_verified', sa.Boolean(), nullable=True),
        sa.Column('two_factor_enabled', sa.Boolean(), nullable=True),
        sa.Column('language_preference', sa.String(), nullable=True),
        sa.Column('data_encrypted', sa.Boolean(), nullable=True),
        sa.Column('encryption_key_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(), nullable=True),
        sa.Column('completed_offers_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('current_rank_key', sa.String(length=50), nullable=True),
        sa.Column('current_rank_title', sa.String(length=100), nullable=True),
        sa.Column('rank_updated_at', sa.DateTime(), nullable=True),
        sa.Column('company_logo', sa.String(length=255), nullable=True),
        sa.Column('company_logo_advertising_consent', sa.Boolean(), nullable=True, server_default='false'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # Create projects table
    op.create_table('projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('project_type', sa.Enum('residential', 'commercial', 'industrial', 'renovation', name='projecttype'), nullable=False),
        sa.Column('status', sa.Enum('planning', 'active', 'completed', 'cancelled', 'on_hold', name='projectstatus'), nullable=False),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('address_street', sa.String(), nullable=True),
        sa.Column('address_zip', sa.String(), nullable=True),
        sa.Column('address_city', sa.String(), nullable=True),
        sa.Column('address_country', sa.String(), nullable=True),
        sa.Column('address_latitude', sa.Float(), nullable=True),
        sa.Column('address_longitude', sa.Float(), nullable=True),
        sa.Column('address_geocoded', sa.Boolean(), nullable=True),
        sa.Column('address_geocoding_date', sa.DateTime(), nullable=True),
        sa.Column('property_size', sa.Float(), nullable=True),
        sa.Column('construction_area', sa.Float(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('estimated_duration', sa.Integer(), nullable=True),
        sa.Column('budget', sa.Float(), nullable=True),
        sa.Column('current_costs', sa.Float(), nullable=True),
        sa.Column('progress_percentage', sa.Float(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('allow_quotes', sa.Boolean(), nullable=True),
        sa.Column('construction_phase', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], )
    )

    # Create milestones table
    op.create_table('milestones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'in_progress', 'completed', 'cancelled', 'on_hold', name='milestonestatus'), nullable=False),
        sa.Column('priority', sa.Enum('low', 'medium', 'high', 'critical', name='milestonepriority'), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('estimated_duration', sa.Integer(), nullable=True),
        sa.Column('actual_duration', sa.Integer(), nullable=True),
        sa.Column('progress_percentage', sa.Float(), nullable=True),
        sa.Column('budget', sa.Float(), nullable=True),
        sa.Column('actual_costs', sa.Float(), nullable=True),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('construction_phase', sa.String(), nullable=True),
        sa.Column('trade_category', sa.String(), nullable=True),
        sa.Column('trade_subcategory', sa.String(), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('attachments', sa.JSON(), nullable=True),
        sa.Column('documents', sa.JSON(), nullable=True),
        sa.Column('shared_documents', sa.JSON(), nullable=True),
        sa.Column('is_archived', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('archived_at', sa.DateTime(), nullable=True),
        sa.Column('archived_by', sa.Integer(), nullable=True),
        sa.Column('archive_reason', sa.Text(), nullable=True),
        sa.Column('completion_date', sa.DateTime(), nullable=True),
        sa.Column('completion_notes', sa.Text(), nullable=True),
        sa.Column('quality_rating', sa.Float(), nullable=True),
        sa.Column('defects_found', sa.Boolean(), nullable=True),
        sa.Column('defects_resolved', sa.Boolean(), nullable=True),
        sa.Column('defects_resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('has_unread_messages', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('has_unread_messages_bautraeger', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('has_unread_messages_dienstleister', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('submission_deadline', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['archived_by'], ['users.id'], )
    )

    # Create tasks table
    op.create_table('tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'in_progress', 'completed', 'cancelled', name='taskstatus'), nullable=False),
        sa.Column('priority', sa.Enum('low', 'medium', 'high', 'urgent', name='taskpriority'), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('estimated_hours', sa.Float(), nullable=True),
        sa.Column('actual_hours', sa.Float(), nullable=True),
        sa.Column('progress_percentage', sa.Integer(), nullable=True),
        sa.Column('is_milestone', sa.Boolean(), nullable=True),
        sa.Column('milestone_id', sa.Integer(), nullable=True),
        sa.Column('archived_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], )
    )

    # Create documents table
    op.create_table('documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(), nullable=True),
        sa.Column('document_type', sa.Enum('plan', 'contract', 'invoice', 'photo', 'report', 'other', name='documenttype'), nullable=False),
        sa.Column('category', sa.Enum('architectural', 'structural', 'electrical', 'plumbing', 'hvac', 'other', name='documentcategory'), nullable=True),
        sa.Column('subcategory', sa.String(), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('version_number', sa.String(length=50), nullable=True),
        sa.Column('version_major', sa.Integer(), nullable=True),
        sa.Column('version_minor', sa.Integer(), nullable=True),
        sa.Column('version_patch', sa.Integer(), nullable=True),
        sa.Column('is_latest_version', sa.Boolean(), nullable=True),
        sa.Column('parent_document_id', sa.Integer(), nullable=True),
        sa.Column('document_status', sa.Enum('draft', 'pending_review', 'approved', 'rejected', 'archived', name='documentstatus'), nullable=True),
        sa.Column('workflow_stage', sa.Enum('draft', 'review', 'approval', 'published', 'archived', name='workflowstage'), nullable=True),
        sa.Column('approval_status', sa.Enum('pending', 'approved', 'rejected', 'requires_changes', name='approvalstatus'), nullable=True),
        sa.Column('review_status', sa.Enum('not_reviewed', 'in_review', 'reviewed', 'requires_revision', name='reviewstatus'), nullable=True),
        sa.Column('locked_by', sa.Integer(), nullable=True),
        sa.Column('locked_at', sa.DateTime(), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('rejected_by', sa.Integer(), nullable=True),
        sa.Column('rejected_at', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('archived_at', sa.DateTime(), nullable=True),
        sa.Column('checksum', sa.String(length=255), nullable=True),
        sa.Column('file_format_version', sa.String(length=50), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('access_level', sa.Enum('read', 'write', 'admin', 'owner', name='accesslevel'), nullable=True),
        sa.Column('sharing_permissions', sa.Text(), nullable=True),
        sa.Column('download_count', sa.Integer(), nullable=True),
        sa.Column('last_accessed_by', sa.Integer(), nullable=True),
        sa.Column('last_accessed_at', sa.DateTime(), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('is_favorite', sa.Boolean(), nullable=True),
        sa.Column('hidden_for_service_providers', sa.Boolean(), nullable=True, server_default='false'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['locked_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['rejected_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['last_accessed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['parent_document_id'], ['documents.id'], )
    )

    # Create quotes table
    op.create_table('quotes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('milestone_id', sa.Integer(), nullable=True),
        sa.Column('service_provider_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('draft', 'submitted', 'accepted', 'rejected', 'expired', name='quotestatus'), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.Column('labor_cost', sa.Float(), nullable=True),
        sa.Column('material_cost', sa.Float(), nullable=True),
        sa.Column('overhead_cost', sa.Float(), nullable=True),
        sa.Column('estimated_duration', sa.Integer(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('completion_date', sa.Date(), nullable=True),
        sa.Column('payment_terms', sa.Text(), nullable=True),
        sa.Column('warranty_period', sa.Integer(), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('price_deviation', sa.Float(), nullable=True),
        sa.Column('ai_recommendation', sa.String(), nullable=True),
        sa.Column('contact_released', sa.Boolean(), nullable=True),
        sa.Column('contact_released_at', sa.DateTime(), nullable=True),
        sa.Column('quote_number', sa.String(), nullable=True),
        sa.Column('company_name', sa.String(), nullable=True),
        sa.Column('contact_person', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('website', sa.String(), nullable=True),
        sa.Column('qualifications', sa.Text(), nullable=True),
        sa.Column('references', sa.Text(), nullable=True),
        sa.Column('certifications', sa.Text(), nullable=True),
        sa.Column('technical_approach', sa.Text(), nullable=True),
        sa.Column('quality_standards', sa.Text(), nullable=True),
        sa.Column('safety_measures', sa.Text(), nullable=True),
        sa.Column('environmental_compliance', sa.Text(), nullable=True),
        sa.Column('risk_assessment', sa.Text(), nullable=True),
        sa.Column('contingency_plan', sa.Text(), nullable=True),
        sa.Column('additional_notes', sa.Text(), nullable=True),
        sa.Column('pdf_upload_path', sa.String(), nullable=True),
        sa.Column('additional_documents', sa.Text(), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('revised_after_inspection', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('revision_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('last_revised_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('is_revised_quote', sa.Boolean(), nullable=True, server_default='false'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], ),
        sa.ForeignKeyConstraint(['service_provider_id'], ['users.id'], )
    )

    # Create appointments table
    op.create_table('appointments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('milestone_id', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('appointment_type', sa.Enum('inspection', 'meeting', 'delivery', 'maintenance', name='appointmenttype'), nullable=False),
        sa.Column('status', sa.Enum('scheduled', 'confirmed', 'in_progress', 'completed', 'cancelled', 'rescheduled', name='appointmentstatus'), nullable=False),
        sa.Column('scheduled_date', sa.DateTime(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('invited_service_providers', sa.JSON(), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('location_details', sa.Text(), nullable=True),
        sa.Column('contact_person', sa.String(), nullable=True),
        sa.Column('contact_phone', sa.String(), nullable=True),
        sa.Column('preparation_notes', sa.Text(), nullable=True),
        sa.Column('responses', sa.JSON(), nullable=True),
        sa.Column('inspection_completed', sa.Boolean(), nullable=True),
        sa.Column('selected_service_provider_id', sa.Integer(), nullable=True),
        sa.Column('inspection_notes', sa.Text(), nullable=True),
        sa.Column('inspection_photos', sa.JSON(), nullable=True),
        sa.Column('requires_renegotiation', sa.Boolean(), nullable=True),
        sa.Column('renegotiation_details', sa.Text(), nullable=True),
        sa.Column('calendar_event_data', sa.JSON(), nullable=True),
        sa.Column('notification_sent', sa.Boolean(), nullable=True),
        sa.Column('follow_up_notification_date', sa.DateTime(), nullable=True),
        sa.Column('follow_up_sent', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['selected_service_provider_id'], ['users.id'], )
    )

    # Create acceptances table
    op.create_table('acceptances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('milestone_id', sa.Integer(), nullable=False),
        sa.Column('appointment_id', sa.Integer(), nullable=True),
        sa.Column('contractor_id', sa.Integer(), nullable=False),
        sa.Column('service_provider_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('acceptance_type', sa.Enum('quality', 'completion', 'final', 'partial', name='acceptancetype'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'in_progress', 'accepted', 'rejected', 'requires_revision', name='acceptancestatus'), nullable=False),
        sa.Column('scheduled_date', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('accepted', sa.Boolean(), nullable=True),
        sa.Column('acceptance_notes', sa.Text(), nullable=True),
        sa.Column('contractor_notes', sa.Text(), nullable=True),
        sa.Column('service_provider_notes', sa.Text(), nullable=True),
        sa.Column('quality_rating', sa.Integer(), nullable=True),
        sa.Column('timeliness_rating', sa.Integer(), nullable=True),
        sa.Column('overall_rating', sa.Integer(), nullable=True),
        sa.Column('checklist_data', sa.JSON(), nullable=True),
        sa.Column('review_date', sa.Date(), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('review_task_id', sa.Integer(), nullable=True),
        sa.Column('photos', sa.JSON(), nullable=True),
        sa.Column('documents', sa.JSON(), nullable=True),
        sa.Column('protocol_pdf_path', sa.String(), nullable=True),
        sa.Column('protocol_generated_at', sa.DateTime(), nullable=True),
        sa.Column('warranty_start_date', sa.DateTime(), nullable=True),
        sa.Column('warranty_period_months', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], ),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ),
        sa.ForeignKeyConstraint(['contractor_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['service_provider_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['review_task_id'], ['tasks.id'], )
    )

    # Create invoices table
    op.create_table('invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('milestone_id', sa.Integer(), nullable=False),
        sa.Column('service_provider_id', sa.Integer(), nullable=False),
        sa.Column('invoice_number', sa.String(length=100), nullable=False),
        sa.Column('invoice_date', sa.DateTime(), nullable=False),
        sa.Column('due_date', sa.DateTime(), nullable=False),
        sa.Column('net_amount', sa.Float(), nullable=False),
        sa.Column('vat_rate', sa.Float(), nullable=False),
        sa.Column('vat_amount', sa.Float(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('material_costs', sa.Float(), nullable=True),
        sa.Column('labor_costs', sa.Float(), nullable=True),
        sa.Column('additional_costs', sa.Float(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('work_period_from', sa.DateTime(), nullable=True),
        sa.Column('work_period_to', sa.DateTime(), nullable=True),
        sa.Column('status', sa.Enum('draft', 'sent', 'paid', 'overdue', 'cancelled', name='invoicestatus'), nullable=True),
        sa.Column('type', sa.Enum('invoice', 'credit', name='invoicetype'), nullable=False),
        sa.Column('pdf_file_path', sa.String(length=500), nullable=True),
        sa.Column('pdf_file_name', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('payment_reference', sa.String(length=255), nullable=True),
        sa.Column('rating_quality', sa.Integer(), nullable=True),
        sa.Column('rating_timeliness', sa.Integer(), nullable=True),
        sa.Column('rating_communication', sa.Integer(), nullable=True),
        sa.Column('rating_value', sa.Integer(), nullable=True),
        sa.Column('rating_overall', sa.Integer(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], ),
        sa.ForeignKeyConstraint(['service_provider_id'], ['users.id'], )
    )

    # Create user_credits table
    op.create_table('user_credits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('credits', sa.Integer(), nullable=False),
        sa.Column('plan_status', sa.Enum('free', 'pro', 'premium', name='planstatus'), nullable=False),
        sa.Column('pro_start_date', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_pro_day', sa.DateTime(), nullable=True),
        sa.Column('total_pro_days', sa.Integer(), nullable=True),
        sa.Column('auto_downgrade_enabled', sa.Boolean(), nullable=True),
        sa.Column('low_credit_warning_sent', sa.Boolean(), nullable=True),
        sa.Column('downgrade_notification_sent', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_daily_deduction', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.UniqueConstraint('user_id')
    )

    # Create remaining tables (abbreviated for space - will be completed in next step)
    op.create_table('comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('position_x', sa.Float(), nullable=True),
        sa.Column('position_y', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )

    op.create_table('cost_positions',
        sa.Column('id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('invoice_id', sa.Integer(), nullable=True),
        sa.Column('quote_id', sa.Integer(), nullable=True),
        sa.Column('milestone_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('amount', sa.REAL(), nullable=False, server_default='0.0'),
        sa.Column('position_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('category', sa.Text(), nullable=False, server_default='custom'),
        sa.Column('cost_type', sa.Text(), nullable=False, server_default='standard'),
        sa.Column('status', sa.Text(), nullable=False, server_default='active'),
        sa.Column('contractor_name', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ),
        sa.ForeignKeyConstraint(['quote_id'], ['quotes.id'], ),
        sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], )
    )

    # Create indexes for better performance
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_user_type', 'users', ['user_type'])
    op.create_index('ix_users_status', 'users', ['status'])
    op.create_index('ix_projects_owner_id', 'projects', ['owner_id'])
    op.create_index('ix_projects_status', 'projects', ['status'])
    op.create_index('ix_milestones_project_id', 'milestones', ['project_id'])
    op.create_index('ix_milestones_status', 'milestones', ['status'])
    op.create_index('ix_documents_project_id', 'documents', ['project_id'])
    op.create_index('ix_documents_document_type', 'documents', ['document_type'])
    op.create_index('ix_quotes_project_id', 'quotes', ['project_id'])
    op.create_index('ix_quotes_service_provider_id', 'quotes', ['service_provider_id'])
    op.create_index('ix_quotes_status', 'quotes', ['status'])
    op.create_index('ix_appointments_project_id', 'appointments', ['project_id'])
    op.create_index('ix_appointments_status', 'appointments', ['status'])
    op.create_index('ix_acceptances_project_id', 'acceptances', ['project_id'])
    op.create_index('ix_acceptances_milestone_id', 'acceptances', ['milestone_id'])
    op.create_index('ix_invoices_project_id', 'invoices', ['project_id'])
    op.create_index('ix_invoices_service_provider_id', 'invoices', ['service_provider_id'])
    op.create_index('ix_user_credits_user_id', 'user_credits', ['user_id'], unique=True)

    # Create alembic_version table
    op.create_table('alembic_version',
        sa.Column('version_num', sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint('version_num')
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('alembic_version')
    op.drop_table('user_credits')
    op.drop_table('invoices')
    op.drop_table('acceptances')
    op.drop_table('appointments')
    op.drop_table('quotes')
    op.drop_table('documents')
    op.drop_table('tasks')
    op.drop_table('milestones')
    op.drop_table('projects')
    op.drop_table('users')
    op.drop_table('cost_positions')
    op.drop_table('comments')
    
    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS calendarentrystatus CASCADE")
    op.execute("DROP TYPE IF EXISTS requeststatus CASCADE")
    op.execute("DROP TYPE IF EXISTS allocationstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS resourcevisibility CASCADE")
    op.execute("DROP TYPE IF EXISTS resourcestatus CASCADE")
    op.execute("DROP TYPE IF EXISTS notificationpriority CASCADE")
    op.execute("DROP TYPE IF EXISTS notificationtype CASCADE")
    op.execute("DROP TYPE IF EXISTS visualizationstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS visualizationcategory CASCADE")
    op.execute("DROP TYPE IF EXISTS progressupdatetype CASCADE")
    op.execute("DROP TYPE IF EXISTS invoicetype CASCADE")
    op.execute("DROP TYPE IF EXISTS invoicestatus CASCADE")
    op.execute("DROP TYPE IF EXISTS defectseverity CASCADE")
    op.execute("DROP TYPE IF EXISTS acceptancetype CASCADE")
    op.execute("DROP TYPE IF EXISTS acceptancestatus CASCADE")
    op.execute("DROP TYPE IF EXISTS appointmentstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS appointmenttype CASCADE")
    op.execute("DROP TYPE IF EXISTS inspectioninvitationstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS inspectionstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS purchasestatus CASCADE")
    op.execute("DROP TYPE IF EXISTS crediteventtype CASCADE")
    op.execute("DROP TYPE IF EXISTS planstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS auditaction CASCADE")
    op.execute("DROP TYPE IF EXISTS messagetype CASCADE")
    op.execute("DROP TYPE IF EXISTS quotestatus CASCADE")
    op.execute("DROP TYPE IF EXISTS milestonepriority CASCADE")
    op.execute("DROP TYPE IF EXISTS milestonestatus CASCADE")
    op.execute("DROP TYPE IF EXISTS changetype CASCADE")
    op.execute("DROP TYPE IF EXISTS accesslevel CASCADE")
    op.execute("DROP TYPE IF EXISTS sharetype CASCADE")
    op.execute("DROP TYPE IF EXISTS reviewstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS approvalstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS workflowstage CASCADE")
    op.execute("DROP TYPE IF EXISTS documentstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS documentcategory CASCADE")
    op.execute("DROP TYPE IF EXISTS documenttype CASCADE")
    op.execute("DROP TYPE IF EXISTS taskpriority CASCADE")
    op.execute("DROP TYPE IF EXISTS taskstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS projectstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS projecttype CASCADE")
    op.execute("DROP TYPE IF EXISTS authprovider CASCADE")
    op.execute("DROP TYPE IF EXISTS userrole CASCADE")
    op.execute("DROP TYPE IF EXISTS userstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS usertype CASCADE")