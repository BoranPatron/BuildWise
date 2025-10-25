#!/usr/bin/env python3
"""
Direkte Datenbank-Korrektur für Quote Status Enum-Inkonsistenz
Führt die notwendigen Updates aus, ohne Alembic zu verwenden
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.core.database import get_async_engine


async def fix_quote_status_enum():
    """Fix inconsistent quote status enum values in database"""
    
    print("[INFO] Starting Quote Status Enum Fix...")
    
    try:
        # Get database engine
        engine = get_async_engine()
        
        async with engine.begin() as conn:
            print("[INFO] Connected to database")
            
            # Check current quote statuses
            result = await conn.execute(text("SELECT DISTINCT status FROM quotes WHERE status IS NOT NULL"))
            current_statuses = [row[0] for row in result.fetchall()]
            print(f"[INFO] Current quote statuses: {current_statuses}")
            
            # Fix quote statuses
            updates_made = 0
            
            # Update ACCEPTED to accepted
            result = await conn.execute(text("UPDATE quotes SET status = 'accepted' WHERE status = 'ACCEPTED'"))
            if result.rowcount > 0:
                print(f"[SUCCESS] Updated {result.rowcount} quotes from ACCEPTED to accepted")
                updates_made += result.rowcount
            
            # Update PENDING to pending
            result = await conn.execute(text("UPDATE quotes SET status = 'pending' WHERE status = 'PENDING'"))
            if result.rowcount > 0:
                print(f"[SUCCESS] Updated {result.rowcount} quotes from PENDING to pending")
                updates_made += result.rowcount
            
            # Update REJECTED to rejected
            result = await conn.execute(text("UPDATE quotes SET status = 'rejected' WHERE status = 'REJECTED'"))
            if result.rowcount > 0:
                print(f"[SUCCESS] Updated {result.rowcount} quotes from REJECTED to rejected")
                updates_made += result.rowcount
            
            # Update WITHDRAWN to withdrawn
            result = await conn.execute(text("UPDATE quotes SET status = 'withdrawn' WHERE status = 'WITHDRAWN'"))
            if result.rowcount > 0:
                print(f"[SUCCESS] Updated {result.rowcount} quotes from WITHDRAWN to withdrawn")
                updates_made += result.rowcount
            
            # Update EXPIRED to expired
            result = await conn.execute(text("UPDATE quotes SET status = 'expired' WHERE status = 'EXPIRED'"))
            if result.rowcount > 0:
                print(f"[SUCCESS] Updated {result.rowcount} quotes from EXPIRED to expired")
                updates_made += result.rowcount
            
            # Check if milestone_progress table exists and fix it too
            try:
                # Check if table exists
                result = await conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'milestone_progress'
                    )
                """))
                table_exists = result.scalar()
                
                if table_exists:
                    print("[INFO] Found milestone_progress table, fixing enum values...")
                    
                    # Fix update_type enum values
                    result = await conn.execute(text("UPDATE milestone_progress SET update_type = 'comment' WHERE update_type = 'COMMENT'"))
                    if result.rowcount > 0:
                        print(f"[SUCCESS] Updated {result.rowcount} milestone_progress from COMMENT to comment")
                        updates_made += result.rowcount
                    
                    result = await conn.execute(text("UPDATE milestone_progress SET update_type = 'completion' WHERE update_type = 'COMPLETION'"))
                    if result.rowcount > 0:
                        print(f"[SUCCESS] Updated {result.rowcount} milestone_progress from COMPLETION to completion")
                        updates_made += result.rowcount
                    
                    result = await conn.execute(text("UPDATE milestone_progress SET update_type = 'revision' WHERE update_type = 'REVISION'"))
                    if result.rowcount > 0:
                        print(f"[SUCCESS] Updated {result.rowcount} milestone_progress from REVISION to revision")
                        updates_made += result.rowcount
                    
                    result = await conn.execute(text("UPDATE milestone_progress SET update_type = 'defect' WHERE update_type = 'DEFECT'"))
                    if result.rowcount > 0:
                        print(f"[SUCCESS] Updated {result.rowcount} milestone_progress from DEFECT to defect")
                        updates_made += result.rowcount
                    
                    # Fix defect_severity enum values
                    result = await conn.execute(text("UPDATE milestone_progress SET defect_severity = 'minor' WHERE defect_severity = 'MINOR'"))
                    if result.rowcount > 0:
                        print(f"[SUCCESS] Updated {result.rowcount} milestone_progress from MINOR to minor")
                        updates_made += result.rowcount
                    
                    result = await conn.execute(text("UPDATE milestone_progress SET defect_severity = 'major' WHERE defect_severity = 'MAJOR'"))
                    if result.rowcount > 0:
                        print(f"[SUCCESS] Updated {result.rowcount} milestone_progress from MAJOR to major")
                        updates_made += result.rowcount
                    
                    result = await conn.execute(text("UPDATE milestone_progress SET defect_severity = 'critical' WHERE defect_severity = 'CRITICAL'"))
                    if result.rowcount > 0:
                        print(f"[SUCCESS] Updated {result.rowcount} milestone_progress from CRITICAL to critical")
                        updates_made += result.rowcount
                else:
                    print("[INFO] milestone_progress table not found, skipping...")
                    
            except Exception as e:
                print(f"[WARNING] Could not update milestone_progress table: {e}")
            
            # Verify the fix
            result = await conn.execute(text("SELECT DISTINCT status FROM quotes WHERE status IS NOT NULL"))
            final_statuses = [row[0] for row in result.fetchall()]
            print(f"[INFO] Final quote statuses: {final_statuses}")
            
            print(f"[SUCCESS] Enum fix completed! Total updates made: {updates_made}")
            
    except Exception as e:
        print(f"[ERROR] Failed to fix enum values: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


async def main():
    """Main function"""
    success = await fix_quote_status_enum()
    if success:
        print("[SUCCESS] Database enum fix completed successfully!")
        sys.exit(0)
    else:
        print("[ERROR] Database enum fix failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
