#!/usr/bin/env python3
"""
Migration: Füge defects_resolved Spalten zur Milestone-Tabelle hinzu
"""

import sqlite3
import os
import sys
from datetime import datetime

def add_defects_resolved_columns():
    """Füge defects_resolved und defects_resolved_at Spalten zur Milestone-Tabelle hinzu"""
    
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Datenbank {db_path} nicht gefunden!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Füge defects_resolved Spalten zur Milestone-Tabelle hinzu...")
        
        # Prüfe ob die Spalten bereits existieren
        cursor.execute("PRAGMA table_info(milestones)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"📋 Vorhandene Spalten: {columns}")
        
        # Füge defects_resolved hinzu, falls nicht vorhanden
        if 'defects_resolved' not in columns:
            cursor.execute("""
                ALTER TABLE milestones 
                ADD COLUMN defects_resolved BOOLEAN DEFAULT FALSE
            """)
            print("✅ Spalte 'defects_resolved' hinzugefügt")
        else:
            print("ℹ️ Spalte 'defects_resolved' bereits vorhanden")
        
        # Füge defects_resolved_at hinzu, falls nicht vorhanden
        if 'defects_resolved_at' not in columns:
            cursor.execute("""
                ALTER TABLE milestones 
                ADD COLUMN defects_resolved_at DATETIME
            """)
            print("✅ Spalte 'defects_resolved_at' hinzugefügt")
        else:
            print("ℹ️ Spalte 'defects_resolved_at' bereits vorhanden")
        
        conn.commit()
        print("✅ Migration erfolgreich abgeschlossen!")
        
    except Exception as e:
        print(f"❌ Fehler bei der Migration: {e}")
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    print("🚀 Starte Migration: defects_resolved Spalten")
    success = add_defects_resolved_columns()
    
    if success:
        print("✅ Migration erfolgreich!")
        sys.exit(0)
    else:
        print("❌ Migration fehlgeschlagen!")
        sys.exit(1)