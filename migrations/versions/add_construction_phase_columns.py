"""Add construction phase columns

Revision ID: add_construction_phase_columns
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_construction_phase_columns'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade migration - Add construction phase columns"""
    
    # Füge construction_phase Spalte hinzu
    op.add_column('projects', sa.Column('construction_phase', sa.String(), nullable=True))
    
    # Füge address_country Spalte hinzu mit Standardwert
    op.add_column('projects', sa.Column('address_country', sa.String(), nullable=True, server_default='Deutschland'))
    
    # Aktualisiere bestehende Projekte mit Standard-Land
    op.execute("""
        UPDATE projects 
        SET address_country = 'Deutschland' 
        WHERE address_country IS NULL OR address_country = '';
    """)


def downgrade():
    """Downgrade migration - Remove construction phase columns"""
    
    # Entferne construction_phase Spalte
    op.drop_column('projects', 'construction_phase')
    
    # Entferne address_country Spalte
    op.drop_column('projects', 'address_country') 