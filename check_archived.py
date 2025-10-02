#!/usr/bin/env python3
"""
Überprüfe archivierte Gewerke in der Datenbank
"""

import sqlite3

def check_archived_milestones():
    try:
        conn = sqlite3.connect('buildwise.db')
        cursor = conn.cursor()
        
        # Prüfe alle Gewerke mit completion_status = "archived"
        cursor.execute("""
            SELECT id, title, completion_status, archived, archived_at, archived_by, archive_reason 
            FROM milestones 
            WHERE completion_status = 'archived' OR archived = 1
        """)
        
        results = cursor.fetchall()
        
        print(f"🔍 Gefundene archivierte Gewerke: {len(results)}")
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
        
        # Prüfe auch alle Gewerke mit completed Status
        cursor.execute("""
            SELECT id, title, completion_status, archived, archived_at 
            FROM milestones 
            WHERE completion_status = 'completed'
        """)
        
        completed_results = cursor.fetchall()
        
        print(f"\n🔍 Gewerke mit Status 'completed': {len(completed_results)}")
        print("=" * 80)
        
        for row in completed_results:
            print(f"ID: {row[0]}, Titel: {row[1]}, Status: {row[2]}, Archived: {row[3]}, Archived_at: {row[4]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    check_archived_milestones()
