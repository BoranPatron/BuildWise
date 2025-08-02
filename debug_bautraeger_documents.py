#!/usr/bin/env python3
"""
Debug-Script um zu testen, welche Daten die Bauträgeransicht bekommt
"""
import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.services.milestone_service import get_milestones_for_project, get_milestone_by_id

async def debug_bautraeger_documents():
    """Debug welche Dokumente die Bauträgeransicht bekommt"""
    
    async with get_db_session() as db:
        print("🔍 Debug: Bauträger-Dokumentenanzeige")
        print("=" * 50)
        
        # Teste mit Projekt 7 (hat normalerweise Milestones)
        project_id = 7
        print(f"📋 Lade Milestones für Projekt {project_id} (Bauträger-Modus)...")
        
        try:
            milestones = await get_milestones_for_project(db, project_id)
            print(f"✅ {len(milestones)} Milestones gefunden")
            
            for milestone in milestones:
                print(f"\n📄 Milestone {milestone['id']}: {milestone['title']}")
                print(f"   Dokumente: {milestone.get('documents', 'Keine')}")
                print(f"   Dokumente Typ: {type(milestone.get('documents'))}")
                
                if milestone.get('documents'):
                    docs = milestone['documents']
                    if isinstance(docs, list):
                        print(f"   📋 {len(docs)} Dokumente gefunden:")
                        for i, doc in enumerate(docs):
                            print(f"      {i+1}. {doc}")
                    elif isinstance(docs, str):
                        try:
                            parsed_docs = json.loads(docs)
                            print(f"   📋 {len(parsed_docs)} Dokumente (JSON-String):")
                            for i, doc in enumerate(parsed_docs):
                                print(f"      {i+1}. {doc}")
                        except:
                            print(f"   ❌ Fehler beim Parsen der JSON-Dokumente: {docs}")
                    else:
                        print(f"   ⚠️ Unbekannter Dokumententyp: {type(docs)}")
                else:
                    print("   ❌ Keine Dokumente gefunden")
                
                # Teste auch den Einzelabruf
                print(f"\n🔍 Teste Einzelabruf für Milestone {milestone['id']}...")
                single_milestone = await get_milestone_by_id(db, milestone['id'])
                if single_milestone:
                    print(f"   ✅ Einzelabruf erfolgreich")
                    print(f"   Dokumente (Einzelabruf): {single_milestone.documents}")
                    print(f"   Dokumente Typ (Einzelabruf): {type(single_milestone.documents)}")
                    print(f"   Shared Document IDs: {getattr(single_milestone, 'shared_document_ids', 'Nicht vorhanden')}")
                else:
                    print("   ❌ Einzelabruf fehlgeschlagen")
                
        except Exception as e:
            print(f"❌ Fehler: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_bautraeger_documents())