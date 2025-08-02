#!/usr/bin/env python3
"""
Skript zum Hinzufügen der echten Dokumente zu Milestone 1
"""

import asyncio
import sqlalchemy.ext.asyncio
import json
from sqlalchemy import text
import os

async def add_real_documents_to_milestone():
    """Fügt die echten Dokumente aus dem storage Verzeichnis zu Milestone 1 hinzu"""
    
    # SQLite-Datenbankverbindung
    database_url = "sqlite+aiosqlite:///buildwise.db"
    engine = sqlalchemy.ext.asyncio.create_async_engine(database_url)
    
    async with engine.begin() as conn:
        try:
            print("🔍 Füge echte Dokumente zu Milestone 1 hinzu...")
            
            # Sammle alle echten Dokumente aus dem storage Verzeichnis
            storage_path = "storage/uploads"
            real_documents = []
            
            if os.path.exists(storage_path):
                for root, dirs, files in os.walk(storage_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, storage_path)
                        file_size = os.path.getsize(file_path)
                        
                        # Bestimme MIME-Type basierend auf Dateiendung
                        if file.endswith('.pdf'):
                            mime_type = 'application/pdf'
                        elif file.endswith('.txt'):
                            mime_type = 'text/plain'
                        elif file.endswith('.doc'):
                            mime_type = 'application/msword'
                        elif file.endswith('.docx'):
                            mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                        else:
                            mime_type = 'application/octet-stream'
                        
                        document_data = {
                            "id": len(real_documents) + 1,
                            "title": file.replace('.', ' ').title(),
                            "file_name": file,
                            "file_path": f"/storage/uploads/{relative_path}",
                            "file_size": file_size,
                            "mime_type": mime_type,
                            "uploaded_at": "2025-01-27T10:00:00"
                        }
                        
                        real_documents.append(document_data)
                        print(f"  📄 {file} ({file_size} bytes) - {mime_type}")
            
            if real_documents:
                # Konvertiere zu JSON
                documents_json = json.dumps(real_documents, ensure_ascii=False)
                
                # Update Milestone 1 mit den echten Dokumenten
                await conn.execute(text("""
                    UPDATE milestones
                    SET documents = :documents
                    WHERE id = 1
                """), {"documents": documents_json})
                
                print(f"\n✅ {len(real_documents)} echte Dokumente zu Milestone 1 hinzugefügt!")
                print(f"📄 Dokumente JSON: {documents_json}")
                
                # Überprüfe das Update
                result = await conn.execute(text("""
                    SELECT documents FROM milestones WHERE id = 1
                """))
                
                updated_documents = result.fetchone()[0]
                if updated_documents:
                    documents = json.loads(updated_documents)
                    print(f"\n📋 Überprüfung - Milestone 1 hat jetzt {len(documents)} Dokumente:")
                    for i, doc in enumerate(documents):
                        print(f"  {i+1}. {doc.get('title')} ({doc.get('file_name')})")
            else:
                print("⚠️ Keine Dokumente im storage Verzeichnis gefunden")
            
        except Exception as e:
            print(f"❌ Fehler: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(add_real_documents_to_milestone()) 