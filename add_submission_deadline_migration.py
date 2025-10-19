#!/usr/bin/env python3
"""
Migration: Add submission_deadline column to milestones table
Datum: 2025-01-08
Zweck: Hinzufügung eines optionalen Eingabefeldes für Angebotsfristen bei Ausschreibungen
"""

import sqlite3
import os
from datetime import datetime

def add_submission_deadline_column():
    """Fügt die submission_deadline Spalte zur milestones Tabelle hinzu"""
    
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Datenbank {db_path} nicht gefunden!")
        return False
    
    try:
        # Verbindung zur Datenbank
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Prüfe ob Spalte bereits existiert
        cursor.execute("PRAGMA table_info(milestones)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'submission_deadline' in columns:
            print("Spalte 'submission_deadline' existiert bereits in milestones Tabelle")
            conn.close()
            return True
        
        # Füge die neue Spalte hinzu
        print("Fuege submission_deadline Spalte zur milestones Tabelle hinzu...")
        
        cursor.execute("""
            ALTER TABLE milestones 
            ADD COLUMN submission_deadline DATE NULL
        """)
        
        # Bestätige die Änderung
        conn.commit()
        
        # Prüfe ob Spalte erfolgreich hinzugefügt wurde
        cursor.execute("PRAGMA table_info(milestones)")
        columns_after = [column[1] for column in cursor.fetchall()]
        
        if 'submission_deadline' in columns_after:
            print("Spalte 'submission_deadline' erfolgreich zur milestones Tabelle hinzugefuegt")
            
            # Zeige Spalten-Info
            cursor.execute("SELECT name, type, \"notnull\", dflt_value FROM pragma_table_info('milestones') WHERE name = 'submission_deadline'")
            column_info = cursor.fetchone()
            if column_info:
                print(f"   Spalten-Details: {column_info}")
            
            conn.close()
            return True
        else:
            print("Fehler beim Hinzufuegen der Spalte 'submission_deadline'")
            conn.close()
            return False
            
    except sqlite3.Error as e:
        print(f"SQLite Fehler: {e}")
        if 'conn' in locals():
            conn.close()
        return False
    except Exception as e:
        print(f"Unerwarteter Fehler: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def verify_migration():
    """Verifiziert die Migration"""
    db_path = "buildwise.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Prüfe milestones Tabelle Struktur
        cursor.execute("PRAGMA table_info(milestones)")
        columns = cursor.fetchall()
        
        print("\nAktuelle milestones Tabelle Struktur:")
        print("=" * 60)
        for column in columns:
            cid, name, type_, notnull, default_value, pk = column
            nullable = "NULL" if not notnull else "NOT NULL"
            default = f" DEFAULT {default_value}" if default_value else ""
            pk_indicator = " (PRIMARY KEY)" if pk else ""
            print(f"{cid:2d}. {name:25s} {type_:15s} {nullable:8s}{default}{pk_indicator}")
        
        # Prüfe speziell submission_deadline
        submission_deadline_exists = any(col[1] == 'submission_deadline' for col in columns)
        
        if submission_deadline_exists:
            print(f"\nsubmission_deadline Spalte erfolgreich hinzugefuegt!")
            
            # Teste INSERT mit NULL-Wert
            cursor.execute("""
                INSERT INTO milestones 
                (project_id, created_by, title, description, status, priority, planned_date, submission_deadline)
                VALUES (1, 1, 'Test Milestone', 'Test Description', 'planned', 'medium', '2025-01-15', NULL)
            """)
            
            # Lösche Test-Eintrag wieder
            cursor.execute("DELETE FROM milestones WHERE title = 'Test Milestone'")
            conn.commit()
            
            print("Test-INSERT mit NULL submission_deadline erfolgreich")
        else:
            print("submission_deadline Spalte nicht gefunden!")
        
        conn.close()
        return submission_deadline_exists
        
    except Exception as e:
        print(f"Verifikations-Fehler: {e}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    print("Migration: submission_deadline zu milestones Tabelle hinzufuegen")
    print("=" * 70)
    
    # Führe Migration aus
    success = add_submission_deadline_column()
    
    if success:
        # Verifiziere Migration
        verify_success = verify_migration()
        
        if verify_success:
            print("\nMigration erfolgreich abgeschlossen!")
            print("   - submission_deadline Spalte hinzugefuegt")
            print("   - Spalte akzeptiert NULL-Werte (optional)")
            print("   - Typ: DATE fuer Datumsangaben")
            print("   - Bereit fuer Frontend-Integration")
        else:
            print("\nMigration-Verifikation fehlgeschlagen!")
    else:
        print("\nMigration fehlgeschlagen!")
