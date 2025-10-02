#!/usr/bin/env python3
"""
Migration: Fügt 'title' Spalte zur resources Tabelle hinzu
"""

import sqlite3
import os
from datetime import datetime

def run_migration():
    """Führt die Migration aus"""
    
    # Datenbankpfad
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print(f"FEHLER: Datenbank {db_path} nicht gefunden!")
        return False
    
    try:
        # Verbindung zur Datenbank
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Starte Migration: Füge 'title' Spalte zur resources Tabelle hinzu...")
        
        # Prüfe ob die Spalte bereits existiert
        cursor.execute("PRAGMA table_info(resources)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'title' in columns:
            print("OK: Spalte 'title' existiert bereits in der resources Tabelle")
            return True
        
        # Füge die title Spalte hinzu
        cursor.execute("""
            ALTER TABLE resources 
            ADD COLUMN title VARCHAR(255)
        """)
        
        # Änderungen committen
        conn.commit()
        
        print("Migration erfolgreich abgeschlossen!")
        print("   - Spalte 'title' wurde zur resources Tabelle hinzugefügt")
        
        # Verifikation
        cursor.execute("PRAGMA table_info(resources)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'title' in columns:
            print("Verifikation erfolgreich: 'title' Spalte ist vorhanden")
        else:
            print("Verifikation fehlgeschlagen: 'title' Spalte nicht gefunden")
            return False
        
        return True
        
    except sqlite3.Error as e:
        print(f"SQLite Fehler: {e}")
        return False
    except Exception as e:
        print(f"Unerwarteter Fehler: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("BUILDWISE DATENBANK MIGRATION")
    print("Fügt 'title' Spalte zur resources Tabelle hinzu")
    print("=" * 60)
    
    success = run_migration()
    
    if success:
        print("\nMigration erfolgreich abgeschlossen!")
    else:
        print("\nMigration fehlgeschlagen!")
        exit(1)
