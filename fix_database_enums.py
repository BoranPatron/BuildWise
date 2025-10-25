#!/usr/bin/env python3
"""
Direkte Datenbank-Korrektur für Enum-Inkonsistenzen
Dieses Skript korrigiert die Quote-Status Enum-Werte direkt in der Datenbank
ohne SQLAlchemy zu verwenden.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

def fix_enum_inconsistencies():
    """Korrigiert Enum-Inkonsistenzen direkt in der Datenbank"""
    
    # Hole DATABASE_URL aus der Umgebung
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return False
    
    try:
        # Verbinde zur Datenbank
        print("🔌 Connecting to database...")
        conn = psycopg2.connect(database_url)
        conn.autocommit = True  # Automatische Commits
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("📊 Current quote statuses before fix:")
        cursor.execute("SELECT DISTINCT status FROM quotes WHERE status IS NOT NULL;")
        current_statuses = cursor.fetchall()
        for row in current_statuses:
            print(f"  - {row['status']}")
        
        print("\n🔧 Fixing quote statuses...")
        
        # Korrigiere alle Quote-Status Enum-Werte
        updates = [
            ("UPDATE quotes SET status = 'accepted' WHERE status = 'ACCEPTED'", "ACCEPTED -> accepted"),
            ("UPDATE quotes SET status = 'pending' WHERE status = 'PENDING'", "PENDING -> pending"),
            ("UPDATE quotes SET status = 'rejected' WHERE status = 'REJECTED'", "REJECTED -> rejected"),
            ("UPDATE quotes SET status = 'withdrawn' WHERE status = 'WITHDRAWN'", "WITHDRAWN -> withdrawn"),
            ("UPDATE quotes SET status = 'expired' WHERE status = 'EXPIRED'", "EXPIRED -> expired")
        ]
        
        for sql, description in updates:
            try:
                cursor.execute(sql)
                affected_rows = cursor.rowcount
                print(f"  ✅ {description}: {affected_rows} rows updated")
            except Exception as e:
                print(f"  ⚠️ {description}: {e}")
        
        print("\n📊 Quote statuses after fix:")
        cursor.execute("SELECT DISTINCT status FROM quotes WHERE status IS NOT NULL;")
        fixed_statuses = cursor.fetchall()
        for row in fixed_statuses:
            print(f"  - {row['status']}")
        
        print("\n🔧 Fixing milestone_progress enum values...")
        
        # Korrigiere milestone_progress Enum-Werte falls Tabelle existiert
        milestone_updates = [
            ("UPDATE milestone_progress SET update_type = 'comment' WHERE update_type = 'COMMENT'", "COMMENT -> comment"),
            ("UPDATE milestone_progress SET update_type = 'completion' WHERE update_type = 'COMPLETION'", "COMPLETION -> completion"),
            ("UPDATE milestone_progress SET update_type = 'revision' WHERE update_type = 'REVISION'", "REVISION -> revision"),
            ("UPDATE milestone_progress SET update_type = 'defect' WHERE update_type = 'DEFECT'", "DEFECT -> defect"),
            ("UPDATE milestone_progress SET defect_severity = 'minor' WHERE defect_severity = 'MINOR'", "MINOR -> minor"),
            ("UPDATE milestone_progress SET defect_severity = 'major' WHERE defect_severity = 'MAJOR'", "MAJOR -> major"),
            ("UPDATE milestone_progress SET defect_severity = 'critical' WHERE defect_severity = 'CRITICAL'", "CRITICAL -> critical")
        ]
        
        for sql, description in milestone_updates:
            try:
                cursor.execute(sql)
                affected_rows = cursor.rowcount
                print(f"  ✅ {description}: {affected_rows} rows updated")
            except Exception as e:
                print(f"  ⚠️ {description}: {e}")
        
        print("\n✅ Database enum fix completed!")
        print("📊 Final quote statuses:")
        cursor.execute("SELECT DISTINCT status FROM quotes WHERE status IS NOT NULL;")
        final_statuses = cursor.fetchall()
        for row in final_statuses:
            print(f"  - {row['status']}")
        
        print("\n🎉 All enum inconsistencies have been fixed!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing enum inconsistencies: {e}")
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()
            print("🔌 Database connection closed")

if __name__ == "__main__":
    print("🚀 Starting direct database enum fix...")
    success = fix_enum_inconsistencies()
    if success:
        print("\n✅ Fix completed successfully!")
        exit(0)
    else:
        print("\n❌ Fix failed!")
        exit(1)
