#!/usr/bin/env python3
"""
Datenbank-Migration: Task-Integration für Mängel und Wiedervorlage
- Fügt task_id zu acceptance_defects hinzu (Mangel -> Dienstleister Task)
- Fügt review_task_id zu acceptances hinzu (Wiedervorlage -> Bauträger Task)
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
        
        print("🚀 Starte Defect-Task-Integration Migration...")
        
        # 1. Prüfe ob acceptance_defects Tabelle existiert
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='acceptance_defects'")
        if not cursor.fetchone():
            print("⏭️ acceptance_defects Tabelle existiert nicht - wird übersprungen")
        else:
            # Prüfe ob task_id Spalte bereits existiert
            cursor.execute("PRAGMA table_info(acceptance_defects)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'task_id' not in columns:
                print("➕ Füge task_id Spalte zu acceptance_defects hinzu...")
                cursor.execute("""
                    ALTER TABLE acceptance_defects 
                    ADD COLUMN task_id INTEGER 
                    REFERENCES tasks(id) ON DELETE SET NULL
                """)
                print("✅ task_id Spalte zu acceptance_defects hinzugefügt")
            else:
                print("⏭️ task_id Spalte bereits in acceptance_defects vorhanden")
        
        # 2. Prüfe ob acceptances Tabelle existiert
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='acceptances'")
        if not cursor.fetchone():
            print("⏭️ acceptances Tabelle existiert nicht - wird übersprungen")
        else:
            # Prüfe ob review_task_id Spalte bereits existiert
            cursor.execute("PRAGMA table_info(acceptances)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'review_task_id' not in columns:
                print("➕ Füge review_task_id Spalte zu acceptances hinzu...")
                cursor.execute("""
                    ALTER TABLE acceptances 
                    ADD COLUMN review_task_id INTEGER 
                    REFERENCES tasks(id) ON DELETE SET NULL
                """)
                print("✅ review_task_id Spalte zu acceptances hinzugefügt")
            else:
                print("⏭️ review_task_id Spalte bereits in acceptances vorhanden")
        
        # 3. Commit der Änderungen
        conn.commit()
        print("💾 Änderungen gespeichert")
        
        # 4. Verifikation
        print("\n🔍 Verifikation der Migration:")
        
        # Prüfe acceptance_defects
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='acceptance_defects'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(acceptance_defects)")
            defect_columns = [col[1] for col in cursor.fetchall()]
            print(f"📋 acceptance_defects Spalten: {defect_columns}")
            
            if 'task_id' in defect_columns:
                print("✅ task_id erfolgreich zu acceptance_defects hinzugefügt")
            else:
                print("❌ task_id fehlt in acceptance_defects")
        
        # Prüfe acceptances
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='acceptances'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(acceptances)")
            acceptance_columns = [col[1] for col in cursor.fetchall()]
            print(f"📋 acceptances Spalten: {acceptance_columns}")
            
            if 'review_task_id' in acceptance_columns:
                print("✅ review_task_id erfolgreich zu acceptances hinzugefügt")
            else:
                print("❌ review_task_id fehlt in acceptances")
        
        print("\n✅ Migration erfolgreich abgeschlossen!")
        print("📝 Neue Features verfügbar:")
        print("   - Mängel werden automatisch zu Tasks für Dienstleister")
        print("   - Wiedervorlage-Tasks für Bauträger bei Abnahme unter Vorbehalt")
        print("   - Vollständige Nachverfolgung von Mangelbehebungen")
        return True
            
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
    print("=" * 70)
    print("🏗️  BuildWise - Defect-Task-Integration Migration")
    print("=" * 70)
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
    
    print("=" * 70)

if __name__ == "__main__":
    main()