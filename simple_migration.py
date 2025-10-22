#!/usr/bin/env python3
"""
Simple Migration Script für submission_deadline
"""

import sqlite3
import os

def add_submission_deadline():
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print(f"Datenbank {db_path} nicht gefunden!")
        return False
    
    try:
        conn = sqlite3.connect(db_path, timeout=30.0)
        cursor = conn.cursor()
        
        # Prüfe ob Spalte bereits existiert
        cursor.execute("PRAGMA table_info(milestones)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'submission_deadline' in columns:
            print("Spalte 'submission_deadline' existiert bereits")
            conn.close()
            return True
        
        # Füge Spalte hinzu
        print("Fuege submission_deadline Spalte hinzu...")
        cursor.execute("ALTER TABLE milestones ADD COLUMN submission_deadline DATE NULL")
        conn.commit()
        
        # Verifiziere
        cursor.execute("PRAGMA table_info(milestones)")
        columns_after = [column[1] for column in cursor.fetchall()]
        
        if 'submission_deadline' in columns_after:
            print("Spalte erfolgreich hinzugefuegt!")
            conn.close()
            return True
        else:
            print("Fehler beim Hinzufuegen der Spalte")
            conn.close()
            return False
            
    except sqlite3.Error as e:
        print(f"SQLite Fehler: {e}")
        if 'conn' in locals():
            conn.close()
        return False
    except Exception as e:
        print(f"Fehler: {e}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    success = add_submission_deadline()
    if success:
        print("Migration erfolgreich!")
    else:
        print("Migration fehlgeschlagen!")








