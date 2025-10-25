"""Fix Quote Status Enum Inconsistency

Revision ID: fix_quote_status_enum
Revises: 
Create Date: 2025-10-25 08:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_quote_status_enum'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Fix inconsistent quote status enum values"""
    
    # Update all uppercase enum values to lowercase
    op.execute("""
        UPDATE quotes 
        SET status = 'accepted' 
        WHERE status = 'ACCEPTED'
    """)
    
    op.execute("""
        UPDATE quotes 
        SET status = 'pending' 
        WHERE status = 'PENDING'
    """)
    
    op.execute("""
        UPDATE quotes 
        SET status = 'rejected' 
        WHERE status = 'REJECTED'
    """)
    
    op.execute("""
        UPDATE quotes 
        SET status = 'withdrawn' 
        WHERE status = 'WITHDRAWN'
    """)
    
    op.execute("""
        UPDATE quotes 
        SET status = 'expired' 
        WHERE status = 'EXPIRED'
    """)
    
    # Also fix any other tables that might have similar issues
    # Check if milestone_progress table exists and has similar issues
    try:
        op.execute("""
            UPDATE milestone_progress 
            SET update_type = 'comment' 
            WHERE update_type = 'COMMENT'
        """)
        
        op.execute("""
            UPDATE milestone_progress 
            SET update_type = 'completion' 
            WHERE update_type = 'COMPLETION'
        """)
        
        op.execute("""
            UPDATE milestone_progress 
            SET update_type = 'revision' 
            WHERE update_type = 'REVISION'
        """)
        
        op.execute("""
            UPDATE milestone_progress 
            SET update_type = 'defect' 
            WHERE update_type = 'DEFECT'
        """)
        
        op.execute("""
            UPDATE milestone_progress 
            SET defect_severity = 'minor' 
            WHERE defect_severity = 'MINOR'
        """)
        
        op.execute("""
            UPDATE milestone_progress 
            SET defect_severity = 'major' 
            WHERE defect_severity = 'MAJOR'
        """)
        
        op.execute("""
            UPDATE milestone_progress 
            SET defect_severity = 'critical' 
            WHERE defect_severity = 'CRITICAL'
        """)
    except Exception as e:
        print(f"[WARNING] Could not update milestone_progress table: {e}")
    
    print("[SUCCESS] Quote status enum values fixed")


def downgrade():
    """Revert enum values back to uppercase (if needed)"""
    
    op.execute("""
        UPDATE quotes 
        SET status = 'ACCEPTED' 
        WHERE status = 'accepted'
    """)
    
    op.execute("""
        UPDATE quotes 
        SET status = 'PENDING' 
        WHERE status = 'pending'
    """)
    
    op.execute("""
        UPDATE quotes 
        SET status = 'REJECTED' 
        WHERE status = 'rejected'
    """)
    
    op.execute("""
        UPDATE quotes 
        SET status = 'WITHDRAWN' 
        WHERE status = 'withdrawn'
    """)
    
    op.execute("""
        UPDATE quotes 
        SET status = 'EXPIRED' 
        WHERE status = 'expired'
    """)
    
    print("[SUARNING] Quote status enum values reverted to uppercase")
