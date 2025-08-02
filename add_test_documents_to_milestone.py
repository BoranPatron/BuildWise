#!/usr/bin/env python3
"""
Script um Testdokumente für ein Milestone zu erstellen
"""

import asyncio
import aiosqlite
import json
from datetime import datetime

async def add_test_documents_to_milestone():
    """Fügt Test-Dokumente zu einem Milestone hinzu"""
    
    async with aiosqlite.connect('buildwise.db') as db:
        print("🔧 Verbunden zur SQLite-Datenbank")
        
        # Test-Dokumente für Milestone ID 1 (TEST_Bodenlegen)
        test_documents = [
            {
                "id": 1,
                "title": "Bodenlegen Plan",
                "file_name": "bodenlegen_plan.pdf",
                "file_path": "/storage/uploads/project_7/bodenlegen_plan.pdf",
                "file_size": 2048576,
                "mime_type": "application/pdf",
                "uploaded_at": "2025-08-01T09:00:00"
            },
            {
                "id": 2,
                "title": "Technische Zeichnung Boden",
                "file_name": "technische_zeichnung_boden.pdf",
                "file_path": "/storage/uploads/project_7/technische_zeichnung_boden.pdf",
                "file_size": 1536000,
                "mime_type": "application/pdf",
                "uploaded_at": "2025-08-01T09:30:00"
            },
            {
                "id": 3,
                "title": "Materialliste Boden",
                "file_name": "materialliste_boden.xlsx",
                "file_path": "/storage/uploads/project_7/materialliste_boden.xlsx",
                "file_size": 512000,
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "uploaded_at": "2025-08-01T10:00:00"
            }
        ]
        
        # Konvertiere zu JSON-String
        documents_json = json.dumps(test_documents)
        
        try:
            # Update Milestone ID 1 mit Test-Dokumenten
            cursor = await db.execute("""
                UPDATE milestones 
                SET documents = ? 
                WHERE id = ?
            """, (documents_json, 1))
            
            await db.commit()
            print("✅ Test-Dokumente erfolgreich zu Milestone ID 1 hinzugefügt!")
            print(f"📋 Anzahl Dokumente: {len(test_documents)}")
            
            # Überprüfe das Update
            cursor = await db.execute("""
                SELECT id, title, documents 
                FROM milestones 
                WHERE id = ?
            """, (1,))
            
            milestone = await cursor.fetchone()
            if milestone:
                print(f"📋 Milestone ID {milestone[0]}: {milestone[1]}")
                documents = json.loads(milestone[2]) if milestone[2] else []
                print(f"📄 Anzahl Dokumente: {len(documents)}")
                for doc in documents:
                    print(f"  - {doc.get('title', 'Unbekannt')} ({doc.get('file_name', 'Unbekannt')})")
            
        except Exception as e:
            print(f"❌ Fehler beim Hinzufügen der Test-Dokumente: {e}")

if __name__ == "__main__":
    asyncio.run(add_test_documents_to_milestone()) 