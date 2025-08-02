#!/usr/bin/env python3
"""
Skript zum Überprüfen aller Dokumente in der Datenbank
"""

import asyncio
import sqlalchemy.ext.asyncio
import json
from sqlalchemy import text

async def check_database_documents():
    """Überprüft alle Dokumente in der Datenbank"""
    
    # SQLite-Datenbankverbindung
    database_url = "sqlite+aiosqlite:///buildwise.db"
    engine = sqlalchemy.ext.asyncio.create_async_engine(database_url)
    
    async with engine.begin() as conn:
        try:
            print("🔍 Überprüfe alle Dokumente in der Datenbank...")
            
            # 1. Überprüfe Milestones und ihre Dokumente
            print("\n📋 Milestones und ihre Dokumente:")
            result = await conn.execute(text("""
                SELECT id, title, documents, project_id 
                FROM milestones 
                ORDER BY id
            """))
            
            milestones = result.fetchall()
            print(f"✅ {len(milestones)} Milestones gefunden")
            
            for milestone in milestones:
                milestone_id, title, documents_json, project_id = milestone
                print(f"\n📋 Milestone {milestone_id}: {title} (Projekt: {project_id})")
                
                if documents_json:
                    try:
                        documents = json.loads(documents_json)
                        print(f"    Dokumente: {len(documents)}")
                        for i, doc in enumerate(documents):
                            if isinstance(doc, dict):
                                print(f"      {i+1}. {doc.get('title', doc.get('name', 'Unbekannt'))}")
                                print(f"         Type: {doc.get('type', doc.get('mime_type', 'Unbekannt'))}")
                                print(f"         Size: {doc.get('size', doc.get('file_size', 'Unbekannt'))}")
                            else:
                                print(f"      {i+1}. {doc} (kein Dictionary)")
                    except json.JSONDecodeError:
                        print(f"    ⚠️ Ungültige JSON-Daten: {documents_json}")
                else:
                    print(f"    ⚠️ Keine Dokumente")
            
            # 2. Überprüfe alle Dokumente in der documents Tabelle (falls vorhanden)
            print("\n📄 Alle Dokumente in der documents Tabelle:")
            try:
                result = await conn.execute(text("""
                    SELECT id, title, file_name, file_path, file_size, mime_type, uploaded_at
                    FROM documents 
                    ORDER BY id
                """))
                
                documents = result.fetchall()
                print(f"✅ {len(documents)} Dokumente in der documents Tabelle gefunden")
                
                for doc in documents:
                    doc_id, title, file_name, file_path, file_size, mime_type, uploaded_at = doc
                    print(f"  📄 {doc_id}: {title} ({file_name})")
                    print(f"     Pfad: {file_path}")
                    print(f"     Größe: {file_size}")
                    print(f"     Type: {mime_type}")
                    print(f"     Upload: {uploaded_at}")
                    
            except Exception as e:
                print(f"⚠️ Keine documents Tabelle gefunden oder Fehler: {e}")
            
            # 3. Überprüfe alle Dateien im storage Verzeichnis
            print("\n📁 Überprüfe storage Verzeichnis...")
            import os
            storage_path = "storage/uploads"
            
            if os.path.exists(storage_path):
                for root, dirs, files in os.walk(storage_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, storage_path)
                        file_size = os.path.getsize(file_path)
                        print(f"  📄 {relative_path} ({file_size} bytes)")
            else:
                print(f"⚠️ Storage Verzeichnis nicht gefunden: {storage_path}")
            
        except Exception as e:
            print(f"❌ Fehler: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_database_documents()) 