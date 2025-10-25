#!/usr/bin/env python3
"""
Atomare Enum-Migration für BuildWise
Führt eine vollständige Enum-Normalisierung durch, bevor der Server startet
"""
import asyncio
import asyncpg
import os
from typing import Dict, List, Tuple

class AtomicEnumMigration:
    def __init__(self):
        # Verwende Umgebungsvariablen für Render-Deployment
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres'),
            'database': os.getenv('DB_NAME', 'buildwise')
        }
        
        print(f"🔗 Database config: {self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}")
    
    async def run_migration(self):
        """Führt die atomare Enum-Migration durch"""
        print("🚀 Starting atomic enum migration...")
        
        conn = None
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            # Starte Transaktion
            async with conn.transaction():
                print("📊 Checking current enum values...")
                await self._check_current_values(conn)
                
                print("🔧 Applying enum fixes...")
                await self._fix_quotes_status(conn)
                await self._fix_milestone_progress_enums(conn)
                await self._fix_milestones_completion_status(conn)
                
                print("✅ Enum migration completed successfully!")
                
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            raise
        finally:
            if conn:
                await conn.close()
    
    async def _check_current_values(self, conn: asyncpg.Connection):
        """Prüft aktuelle Enum-Werte"""
        
        # Quotes status
        quotes_status = await conn.fetch('SELECT DISTINCT status FROM quotes WHERE status IS NOT NULL')
        print(f"📊 Quotes status: {[row['status'] for row in quotes_status]}")
        
        # Milestone progress update_type
        try:
            progress_update_type = await conn.fetch('SELECT DISTINCT update_type FROM milestone_progress WHERE update_type IS NOT NULL')
            print(f"📊 Progress update_type: {[row['update_type'] for row in progress_update_type]}")
        except Exception as e:
            print(f"⚠️ Could not check progress update_type: {e}")
        
        # Milestone progress defect_severity
        try:
            defect_severity = await conn.fetch('SELECT DISTINCT defect_severity FROM milestone_progress WHERE defect_severity IS NOT NULL')
            print(f"📊 Progress defect_severity: {[row['defect_severity'] for row in defect_severity]}")
        except Exception as e:
            print(f"⚠️ Could not check progress defect_severity: {e}")
        
        # Milestones completion_status
        try:
            completion_status = await conn.fetch('SELECT DISTINCT completion_status FROM milestones WHERE completion_status IS NOT NULL')
            print(f"📊 Milestones completion_status: {[row['completion_status'] for row in completion_status]}")
        except Exception as e:
            print(f"⚠️ Could not check milestones completion_status: {e}")
    
    async def _fix_quotes_status(self, conn: asyncpg.Connection):
        """Korrigiert quotes.status Enum-Werte"""
        print("🔧 Fixing quotes.status...")
        
        fixes = [
            ('ACCEPTED', 'accepted'),
            ('PENDING', 'pending'),
            ('REJECTED', 'rejected'),
            ('WITHDRAWN', 'withdrawn'),
            ('EXPIRED', 'expired')
        ]
        
        for old_val, new_val in fixes:
            result = await conn.execute(
                f"UPDATE quotes SET status = $1 WHERE status = $2",
                new_val, old_val
            )
            if result.split()[-1] != '0':
                print(f"  ✅ Updated {result.split()[-1]} quotes from {old_val} to {new_val}")
    
    async def _fix_milestone_progress_enums(self, conn: asyncpg.Connection):
        """Korrigiert milestone_progress Enum-Werte"""
        print("🔧 Fixing milestone_progress enums...")
        
        # Update type fixes
        update_type_fixes = [
            ('COMMENT', 'comment'),
            ('COMPLETION', 'completion'),
            ('REVISION', 'revision'),
            ('DEFECT', 'defect')
        ]
        
        for old_val, new_val in update_type_fixes:
            result = await conn.execute(
                f"UPDATE milestone_progress SET update_type = $1 WHERE update_type = $2",
                new_val, old_val
            )
            if result.split()[-1] != '0':
                print(f"  ✅ Updated {result.split()[-1]} progress updates from {old_val} to {new_val}")
        
        # Defect severity fixes
        defect_severity_fixes = [
            ('MINOR', 'minor'),
            ('MAJOR', 'major'),
            ('CRITICAL', 'critical')
        ]
        
        for old_val, new_val in defect_severity_fixes:
            result = await conn.execute(
                f"UPDATE milestone_progress SET defect_severity = $1 WHERE defect_severity = $2",
                new_val, old_val
            )
            if result.split()[-1] != '0':
                print(f"  ✅ Updated {result.split()[-1]} defect severities from {old_val} to {new_val}")
    
    async def _fix_milestones_completion_status(self, conn: asyncpg.Connection):
        """Korrigiert milestones.completion_status Enum-Werte"""
        print("🔧 Fixing milestones.completion_status...")
        
        completion_status_fixes = [
            ('IN_PROGRESS', 'in_progress'),
            ('COMPLETION_REQUESTED', 'completion_requested'),
            ('UNDER_REVIEW', 'under_review'),
            ('COMPLETED', 'completed'),
            ('COMPLETED_WITH_DEFECTS', 'completed_with_defects')
        ]
        
        for old_val, new_val in completion_status_fixes:
            result = await conn.execute(
                f"UPDATE milestones SET completion_status = $1 WHERE completion_status = $2",
                new_val, old_val
            )
            if result.split()[-1] != '0':
                print(f"  ✅ Updated {result.split()[-1]} milestones from {old_val} to {new_val}")

async def main():
    migration = AtomicEnumMigration()
    await migration.run_migration()

if __name__ == "__main__":
    asyncio.run(main())
