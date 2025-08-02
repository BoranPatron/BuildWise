#!/usr/bin/env python3
"""
Test-Skript für die Erstellung von Milestones mit Dokumenten
"""

import asyncio
import aiosqlite
import json
from datetime import datetime
from pathlib import Path

async def test_milestone_creation_with_documents():
    """Testet die Erstellung eines Milestones mit Dokumenten"""
    
    # Verbinde zur Datenbank
    db_path = "buildwise.db"
    async with aiosqlite.connect(db_path) as db:
        print("🔍 Teste Milestone-Erstellung mit Dokumenten...")
        
        # Prüfe aktuelle Milestones
        cursor = await db.execute("""
            SELECT id, title, documents, created_at 
            FROM milestones 
            ORDER BY id DESC 
            LIMIT 5
        """)
        milestones = await cursor.fetchall()
        
        print(f"📋 Aktuelle Milestones in der Datenbank:")
        for milestone in milestones:
            milestone_id, title, documents, created_at = milestone
            print(f"  ID: {milestone_id}, Titel: {title}")
            print(f"    Erstellt: {created_at}")
            print(f"    Documents: {documents}")
            print(f"    Documents Type: {type(documents)}")
            
            # Versuche JSON zu parsen
            if documents:
                try:
                    parsed_docs = json.loads(documents)
                    print(f"    Parsed Documents: {len(parsed_docs)} Dokumente")
                    for i, doc in enumerate(parsed_docs):
                        if isinstance(doc, dict):
                            doc_name = doc.get('title', doc.get('name', 'Unbekannt'))
                        else:
                            doc_name = str(doc)
                        print(f"      {i+1}. {doc_name}")
                except json.JSONDecodeError as e:
                    print(f"    ❌ JSON Parse Error: {e}")
            else:
                print(f"    ⚠️ Keine Dokumente")
            print()
        
        # Prüfe ob es Dateien im Storage gibt
        storage_path = Path("storage/uploads")
        if storage_path.exists():
            print(f"📁 Storage-Verzeichnis gefunden: {storage_path}")
            for project_dir in storage_path.iterdir():
                if project_dir.is_dir():
                    print(f"  📂 Projekt {project_dir.name}:")
                    for file_path in project_dir.iterdir():
                        if file_path.is_file():
                            print(f"    📄 {file_path.name} ({file_path.stat().st_size} bytes)")
        else:
            print(f"⚠️ Storage-Verzeichnis nicht gefunden: {storage_path}")

if __name__ == "__main__":
    asyncio.run(test_milestone_creation_with_documents()) 