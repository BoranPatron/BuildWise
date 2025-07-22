"""Add construction_phase to milestones table

Revision ID: add_construction_phase_to_milestones
Revises: add_construction_phase_to_cost_positions
Create Date: 2024-01-15 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_construction_phase_to_milestones'
down_revision = 'add_construction_phase_to_cost_positions'
branch_labels = None
depends_on = None


def upgrade():
    """Add construction_phase column to milestones table"""
    # Add construction_phase column
    op.add_column('milestones', sa.Column('construction_phase', sa.String(), nullable=True))
    
    # Add index for better performance
    op.create_index(op.f('ix_milestones_construction_phase'), 'milestones', ['construction_phase'], unique=False)
    
    # Update existing milestones with construction_phase from their projects
    op.execute("""
        UPDATE milestones 
        SET construction_phase = (
            SELECT construction_phase 
            FROM projects 
            WHERE projects.id = milestones.project_id
        )
        WHERE construction_phase IS NULL
    """)


def downgrade():
    """Remove construction_phase column from milestones table"""
    # Drop index
    op.drop_index(op.f('ix_milestones_construction_phase'), table_name='milestones')
    
    # Drop column
    op.drop_column('milestones', 'construction_phase') 