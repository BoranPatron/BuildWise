"""Add construction_phase to cost_positions table

Revision ID: add_construction_phase_to_cost_positions
Revises: fix_buildwise_fees_datetime_columns
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_construction_phase_to_cost_positions'
down_revision = 'fix_buildwise_fees_datetime_columns'
branch_labels = None
depends_on = None


def upgrade():
    """Add construction_phase column to cost_positions table"""
    # Add construction_phase column
    op.add_column('cost_positions', sa.Column('construction_phase', sa.String(), nullable=True))
    
    # Add index for better performance
    op.create_index(op.f('ix_cost_positions_construction_phase'), 'cost_positions', ['construction_phase'], unique=False)
    
    # Update existing cost_positions with construction_phase from their projects
    op.execute("""
        UPDATE cost_positions 
        SET construction_phase = (
            SELECT construction_phase 
            FROM projects 
            WHERE projects.id = cost_positions.project_id
        )
        WHERE construction_phase IS NULL
    """)


def downgrade():
    """Remove construction_phase column from cost_positions table"""
    # Drop index
    op.drop_index(op.f('ix_cost_positions_construction_phase'), table_name='cost_positions')
    
    # Drop column
    op.drop_column('cost_positions', 'construction_phase') 