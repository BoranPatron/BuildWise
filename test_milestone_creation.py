import asyncio
import aiosqlite
import json
from datetime import datetime

async def test_milestone_creation():
    """Testet das Erstellen eines Milestones in der SQLite-Datenbank"""
    
    # Verbinde zur SQLite-Datenbank
    async with aiosqlite.connect('buildwise.db') as db:
        print("🔧 Verbunden zur SQLite-Datenbank")
        
        # Prüfe ob die milestones Tabelle existiert
        cursor = await db.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='milestones'
        """)
        table_exists = await cursor.fetchone()
        
        if not table_exists:
            print("❌ milestones Tabelle existiert nicht!")
            return
        
        print("✅ milestones Tabelle existiert")
        
        # Zeige aktuelle Milestones
        cursor = await db.execute("SELECT COUNT(*) FROM milestones")
        count = await cursor.fetchone()
        print(f"📊 Aktuelle Anzahl Milestones: {count[0]}")
        
        # Zeige die letzten 5 Milestones
        cursor = await db.execute("""
            SELECT id, title, category, status, created_at 
            FROM milestones 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        recent_milestones = await cursor.fetchall()
        
        print("📋 Letzte 5 Milestones:")
        for milestone in recent_milestones:
            print(f"  - ID: {milestone[0]}, Titel: {milestone[1]}, Kategorie: {milestone[2]}, Status: {milestone[3]}, Erstellt: {milestone[4]}")
        
        # Teste das Erstellen eines neuen Milestones
        test_milestone = {
            'project_id': 1,  # Angenommen Projekt ID 1 existiert
            'created_by': 1,  # Angenommen User ID 1 existiert
            'title': 'Test Gewerk',
            'description': 'Test Beschreibung',
            'status': 'planned',
            'priority': 'medium',
            'category': 'electrical',
            'planned_date': '2024-12-31',
            'budget': 5000.0,
            'progress_percentage': 0,
            'requires_inspection': False,
            'documents': json.dumps([]),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        try:
            cursor = await db.execute("""
                INSERT INTO milestones (
                    project_id, created_by, title, description, status, priority, 
                    category, planned_date, budget, progress_percentage, 
                    requires_inspection, documents, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                test_milestone['project_id'],
                test_milestone['created_by'],
                test_milestone['title'],
                test_milestone['description'],
                test_milestone['status'],
                test_milestone['priority'],
                test_milestone['category'],
                test_milestone['planned_date'],
                test_milestone['budget'],
                test_milestone['progress_percentage'],
                test_milestone['requires_inspection'],
                test_milestone['documents'],
                test_milestone['created_at'],
                test_milestone['updated_at']
            ))
            
            await db.commit()
            print("✅ Test Milestone erfolgreich erstellt!")
            
            # Zeige die neue Anzahl
            cursor = await db.execute("SELECT COUNT(*) FROM milestones")
            new_count = await cursor.fetchone()
            print(f"📊 Neue Anzahl Milestones: {new_count[0]}")
            
        except Exception as e:
            print(f"❌ Fehler beim Erstellen des Test Milestones: {e}")
            
            # Zeige die Tabellenstruktur
            cursor = await db.execute("PRAGMA table_info(milestones)")
            columns = await cursor.fetchall()
            print("📋 Milestones Tabellenstruktur:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")

if __name__ == "__main__":
    asyncio.run(test_milestone_creation()) 