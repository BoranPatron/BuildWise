#!/usr/bin/env python3
"""
Datenbank-Migration: Task-Erweiterungen für Drag & Drop und Archivierung
- Fügt milestone_id Spalte hinzu (Gewerk-Zuordnung)
- Fügt archived_at Spalte hinzu (Archivierung)
- Erweitert TaskStatus Enum um 'archived'
"""

import sqlite3
import os
from datetime import datetime

def run_migration():
    # Pfad zur Datenbank
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Datenbank {db_path} nicht gefunden!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🚀 Starte Task-Erweiterungen Migration...")
        
        # 1. Prüfe ob Spalten bereits existieren
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"📋 Aktuelle Tasks-Spalten: {columns}")
        
        # 2. Füge milestone_id Spalte hinzu (falls nicht vorhanden)
        if 'milestone_id' not in columns:
            print("➕ Füge milestone_id Spalte hinzu...")
            cursor.execute("""
                ALTER TABLE tasks 
                ADD COLUMN milestone_id INTEGER 
                REFERENCES milestones(id) ON DELETE SET NULL
            """)
            print("✅ milestone_id Spalte hinzugefügt")
        else:
            print("⏭️ milestone_id Spalte bereits vorhanden")
        
        # 3. Füge archived_at Spalte hinzu (falls nicht vorhanden)
        if 'archived_at' not in columns:
            print("➕ Füge archived_at Spalte hinzu...")
            cursor.execute("""
                ALTER TABLE tasks 
                ADD COLUMN archived_at TIMESTAMP
            """)
            print("✅ archived_at Spalte hinzugefügt")
        else:
            print("⏭️ archived_at Spalte bereits vorhanden")
        
        # 4. Commit der Änderungen
        conn.commit()
        print("💾 Änderungen gespeichert")
        
        # 5. Verifikation - Prüfe die neuen Spalten
        print("\n🔍 Verifikation der Migration:")
        cursor.execute("PRAGMA table_info(tasks)")
        updated_columns = cursor.fetchall()
        
        print("📋 Aktualisierte Tasks-Tabelle:")
        for col in updated_columns:
            col_name = col[1]
            col_type = col[2]
            is_nullable = "NULL" if col[3] == 0 else "NOT NULL"
            default_val = f" DEFAULT {col[4]}" if col[4] is not None else ""
            print(f"   - {col_name}: {col_type} {is_nullable}{default_val}")
        
        # 6. Prüfe ob milestone_id und archived_at vorhanden sind
        final_columns = [col[1] for col in updated_columns]
        
        if 'milestone_id' in final_columns and 'archived_at' in final_columns:
            print("\n✅ Migration erfolgreich abgeschlossen!")
            print("📝 Neue Features verfügbar:")
            print("   - Tasks können Gewerken (Milestones) zugeordnet werden")
            print("   - Automatische Archivierung nach 14 Tagen möglich")
            print("   - Drag & Drop Status-Änderungen unterstützt")
            return True
        else:
            print("❌ Migration unvollständig - nicht alle Spalten wurden hinzugefügt")
            return False
            
    except sqlite3.Error as e:
        print(f"❌ Datenbankfehler: {e}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    print("=" * 60)
    print("🏗️  BuildWise - Task-Erweiterungen Migration")
    print("=" * 60)
    print(f"⏰ Gestartet am: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = run_migration()
    
    print()
    if success:
        print("🎉 Migration erfolgreich abgeschlossen!")
        print("💡 Das Backend kann jetzt neugestartet werden.")
    else:
        print("💥 Migration fehlgeschlagen!")
        print("🔧 Bitte prüfen Sie die Fehlermeldungen und versuchen Sie es erneut.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()