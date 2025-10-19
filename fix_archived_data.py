#!/usr/bin/env python3
"""
Korrigiere archivierte Gewerke mit fehlenden Daten
"""

import sqlite3
from datetime import datetime

def fix_archived_data():
    try:
        conn = sqlite3.connect('buildwise.db')
        cursor = conn.cursor()
        
        # Aktualisiere archivierte Gewerke mit fehlenden Daten
        cursor.execute("""
            UPDATE milestones 
            SET archived_by = 'bautraeger', 
                archive_reason = 'Gewerk abgeschlossen und Rechnung bezahlt'
            WHERE (archived = 1 OR completion_status = 'archived') 
            AND (archived_by IS NULL OR archive_reason IS NULL)
        """)
        
        affected_rows = cursor.rowcount
        print(f"✅ {affected_rows} archivierte Gewerke aktualisiert")
        
        # Prüfe das Ergebnis
        cursor.execute("""
            SELECT id, title, completion_status, archived, archived_at, archived_by, archive_reason 
            FROM milestones 
            WHERE completion_status = 'archived' OR archived = 1
        """)
        
        results = cursor.fetchall()
        
        print(f"\n🔍 Aktualisierte archivierte Gewerke: {len(results)}")
        print("=" * 80)
        
        for row in results:
            print(f"ID: {row[0]}")
            print(f"Titel: {row[1]}")
            print(f"Completion Status: {row[2]}")
            print(f"Archived: {row[3]}")
            print(f"Archived At: {row[4]}")
            print(f"Archived By: {row[5]}")
            print(f"Archive Reason: {row[6]}")
            print("-" * 40)
        
        conn.commit()
        conn.close()
        
        print("\n✅ Datenbank-Update erfolgreich abgeschlossen!")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    fix_archived_data()
