import asyncio
import sqlite3
from pathlib import Path

async def migrate_milestones():
    """Migration für Milestone-Tabelle mit allen erforderlichen Feldern"""
    
    db_path = Path("buildwise.db")
    if not db_path.exists():
        print("❌ Datenbank nicht gefunden!")
        return
    
    try:
        # Verbinde zur SQLite-Datenbank
        conn = sqlite3.connect("buildwise.db")
        cursor = conn.cursor()
        
        # Prüfe ob milestones-Tabelle existiert
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='milestones'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ Milestones-Tabelle nicht gefunden!")
            return
        
        # Prüfe welche Spalten existieren
        cursor.execute("PRAGMA table_info(milestones)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"📋 Vorhandene Spalten: {columns}")
        
        # Füge fehlende Spalten hinzu
        missing_columns = []
        
        required_columns = {
            'priority': 'TEXT DEFAULT "medium"',
            'category': 'TEXT',
            'start_date': 'DATE',
            'end_date': 'DATE',
            'budget': 'REAL',
            'actual_costs': 'REAL DEFAULT 0.0',
            'contractor': 'TEXT',
            'progress_percentage': 'INTEGER DEFAULT 0',
            'is_critical': 'BOOLEAN DEFAULT 0',
            'notify_on_completion': 'BOOLEAN DEFAULT 1',
            'notes': 'TEXT',
            'completed_at': 'DATETIME'
        }
        
        for column_name, column_def in required_columns.items():
            if column_name not in columns:
                missing_columns.append((column_name, column_def))
        
        if missing_columns:
            print(f"🔧 Füge {len(missing_columns)} fehlende Spalten hinzu...")
            
            for column_name, column_def in missing_columns:
                try:
                    cursor.execute(f"ALTER TABLE milestones ADD COLUMN {column_name} {column_def}")
                    print(f"✅ Spalte '{column_name}' hinzugefügt")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"⚠️  Spalte '{column_name}' existiert bereits")
                    else:
                        print(f"❌ Fehler beim Hinzufügen von '{column_name}': {e}")
            
            conn.commit()
            print("✅ Migration abgeschlossen!")
        else:
            print("✅ Alle erforderlichen Spalten sind bereits vorhanden!")
        
        # Zeige finale Tabellenstruktur
        cursor.execute("PRAGMA table_info(milestones)")
        final_columns = cursor.fetchall()
        print("\n📋 Finale Tabellenstruktur:")
        for column in final_columns:
            print(f"  - {column[1]} ({column[2]})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Fehler bei der Migration: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    asyncio.run(migrate_milestones()) 