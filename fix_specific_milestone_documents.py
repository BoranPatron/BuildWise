#!/usr/bin/env python3
"""
Skript zum Hinzufügen nur der spezifischen 3 PDF-Dokumente zum Gewerk
"""

import asyncio
import sqlalchemy.ext.asyncio
import json
from sqlalchemy import text
import os

async def fix_specific_milestone_documents():
    """Fügt nur die spezifischen 3 PDF-Dokumente zum Gewerk hinzu"""
    
    # SQLite-Datenbankverbindung
    database_url = "sqlite+aiosqlite:///buildwise.db"
    engine = sqlalchemy.ext.asyncio.create_async_engine(database_url)
    
    async with engine.begin() as conn:
        try:
            print("🔍 Füge nur die spezifischen 3 PDF-Dokumente zum Gewerk hinzu...")
            
            # Sammle nur die 3 spezifischen PDF-Dokumente (die wahrscheinlich beim Erstellen hochgeladen wurden)
            specific_documents = []
            
            # Liste der 3 spezifischen PDF-Dateien (die beim Erstellen des Gewerks hochgeladen wurden)
            specific_files = [
                "buildwise_invoice_1.pdf",
                "buildwise_invoice_2-1.pdf", 
                "buildwise_invoice_3-1.pdf"
            ]
            
            storage_path = "storage/uploads/project_7"
            
            for filename in specific_files:
                file_path = os.path.join(storage_path, filename)
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    
                    document_data = {
                        "id": len(specific_documents) + 1,
                        "title": filename.replace('.', ' ').title(),
                        "file_name": filename,
                        "file_path": f"/storage/uploads/project_7/{filename}",
                        "file_size": file_size,
                        "mime_type": "application/pdf",
                        "uploaded_at": "2025-01-27T10:00:00"
                    }
                    
                    specific_documents.append(document_data)
                    print(f"  📄 {filename} ({file_size} bytes) - application/pdf")
                else:
                    print(f"  ⚠️ Datei nicht gefunden: {filename}")
            
            if specific_documents:
                # Konvertiere zu JSON
                documents_json = json.dumps(specific_documents, ensure_ascii=False)
                
                # Update Milestone 1 mit nur den spezifischen Dokumenten
                await conn.execute(text("""
                    UPDATE milestones
                    SET documents = :documents
                    WHERE id = 1
                """), {"documents": documents_json})
                
                print(f"\n✅ {len(specific_documents)} spezifische Dokumente zu Milestone 1 hinzugefügt!")
                print(f"📄 Dokumente JSON: {documents_json}")
                
                # Überprüfe das Update
                result = await conn.execute(text("""
                    SELECT documents FROM milestones WHERE id = 1
                """))
                
                updated_documents = result.fetchone()[0]
                if updated_documents:
                    documents = json.loads(updated_documents)
                    print(f"\n📋 Überprüfung - Milestone 1 hat jetzt {len(documents)} spezifische Dokumente:")
                    for i, doc in enumerate(documents):
                        print(f"  {i+1}. {doc.get('title')} ({doc.get('file_name')})")
            else:
                print("⚠️ Keine spezifischen Dokumente gefunden")
            
        except Exception as e:
            print(f"❌ Fehler: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_specific_milestone_documents()) 