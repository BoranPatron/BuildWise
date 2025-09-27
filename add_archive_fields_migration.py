#!/usr/bin/env python3
"""
Datenbank-Migration: Archivierungsfelder für Milestones
- Fügt archived_by Spalte hinzu (Wer hat archiviert)
- Fügt archive_reason Spalte hinzu (Grund für Archivierung)
"""

import sqlite3
import os
from pathlib import Path

def run_migration():
    # Finde die Datenbankdatei
    db_path = Path("instance") / "buildwise.db"
    if not db_path.exists():
        db_path = Path("buildwise.db")
    
    if not db_path.exists():
        print("❌ Datenbankdatei nicht gefunden!")
        return False
    
    print(f"🔍 Verwende Datenbank: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 1. Prüfe aktuelle Spalten der milestones Tabelle
        cursor.execute("PRAGMA table_info(milestones)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Aktuelle Spalten: {column_names}")
        
        # 2. Füge archived_by Spalte hinzu (falls nicht vorhanden)
        if 'archived_by' not in column_names:
            print("➕ Füge archived_by Spalte hinzu...")
            cursor.execute("""
                ALTER TABLE milestones 
                ADD COLUMN archived_by VARCHAR(100)
            """)
            print("✅ archived_by Spalte hinzugefügt")
        else:
            print("⏭️ archived_by Spalte bereits vorhanden")
        
        # 3. Füge archive_reason Spalte hinzu (falls nicht vorhanden)
        if 'archive_reason' not in column_names:
            print("➕ Füge archive_reason Spalte hinzu...")
            cursor.execute("""
                ALTER TABLE milestones 
                ADD COLUMN archive_reason TEXT
            """)
            print("✅ archive_reason Spalte hinzugefügt")
        else:
            print("⏭️ archive_reason Spalte bereits vorhanden")
        
        # 4. Commit der Änderungen
        conn.commit()
        
        # 5. Prüfe finale Spalten
        cursor.execute("PRAGMA table_info(milestones)")
        updated_columns = cursor.fetchall()
        
        print("\n📋 Finale Spalten der milestones Tabelle:")
        for col in updated_columns:
            col_name = col[1]
            col_type = col[2]
            is_nullable = "NULL" if col[3] == 0 else "NOT NULL"
            default_val = f" DEFAULT {col[4]}" if col[4] is not None else ""
            print(f"   - {col_name}: {col_type} {is_nullable}{default_val}")
        
        # 6. Prüfe ob archived_by und archive_reason vorhanden sind
        final_columns = [col[1] for col in updated_columns]
        
        if 'archived_by' in final_columns and 'archive_reason' in final_columns:
            print("\n✅ Migration erfolgreich abgeschlossen!")
            print("📝 Neue Features verfügbar:")
            print("   - archived_by: Speichert wer das Gewerk archiviert hat")
            print("   - archive_reason: Speichert den Grund für die Archivierung")
            return True
        else:
            print("\n❌ Migration fehlgeschlagen - Spalten nicht gefunden!")
            return False
            
    except Exception as e:
        print(f"❌ Fehler bei der Migration: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Starte Migration: Archivierungsfelder für Milestones")
    success = run_migration()
    if success:
        print("\n🎉 Migration erfolgreich abgeschlossen!")
    else:
        print("\n💥 Migration fehlgeschlagen!")
