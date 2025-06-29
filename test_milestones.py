import asyncio
import sqlite3
from pathlib import Path

async def test_milestones():
    """Teste ob Milestones in der Datenbank vorhanden sind"""
    
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
        
        # Hole alle Milestones für Projekt 1
        cursor.execute("SELECT id, title, description, status, priority, category, budget, contractor, progress_percentage FROM milestones WHERE project_id = 1")
        milestones = cursor.fetchall()
        
        print(f"🔍 Gefundene Milestones für Projekt 1: {len(milestones)}")
        
        for milestone in milestones:
            print(f"  - ID: {milestone[0]}")
            print(f"    Titel: {milestone[1]}")
            print(f"    Beschreibung: {milestone[2]}")
            print(f"    Status: {milestone[3]}")
            print(f"    Priorität: {milestone[4]}")
            print(f"    Kategorie: {milestone[5]}")
            print(f"    Budget: {milestone[6]}")
            print(f"    Auftragnehmer: {milestone[7]}")
            print(f"    Fortschritt: {milestone[8]}%")
            print("    ---")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Fehler beim Testen: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    asyncio.run(test_milestones()) 