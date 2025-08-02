#!/usr/bin/env python3
"""
Test-Script um die API-Endpoints zu testen, die die Bauträgeransicht verwendet
"""
import asyncio
import aiohttp
import json

async def test_bautraeger_api():
    """Teste die API-Endpoints für Bauträger"""
    
    base_url = "http://localhost:8000/api/v1"
    
    # Test-Bauträger Login
    login_data = {
        "username": "bautraeger@test.com",
        "password": "password123"
    }
    
    async with aiohttp.ClientSession() as session:
        print("🔐 Login als Bauträger...")
        async with session.post(f"{base_url}/auth/login", json=login_data) as response:
            if response.status == 200:
                login_result = await response.json()
                token = login_result.get("access_token")
                print(f"✅ Login erfolgreich, Token: {token[:20]}...")
                
                headers = {"Authorization": f"Bearer {token}"}
                
                # Teste Milestones für Projekt 7
                project_id = 7
                print(f"\n📋 Lade Milestones für Projekt {project_id}...")
                async with session.get(f"{base_url}/milestones?project_id={project_id}", headers=headers) as milestone_response:
                    if milestone_response.status == 200:
                        milestones = await milestone_response.json()
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
                                        print(f"      {i+1}. ID: {doc.get('id', 'N/A')}, Name: {doc.get('name', doc.get('title', doc.get('file_name', 'Unbekannt')))}")
                                else:
                                    print(f"   ⚠️ Dokumente sind nicht als Liste formatiert: {docs}")
                            else:
                                print("   ❌ Keine Dokumente gefunden")
                            
                            # Teste auch Einzelabruf
                            print(f"\n🔍 Teste Einzelabruf für Milestone {milestone['id']}...")
                            async with session.get(f"{base_url}/milestones/{milestone['id']}", headers=headers) as single_response:
                                if single_response.status == 200:
                                    single_milestone = await single_response.json()
                                    print(f"   ✅ Einzelabruf erfolgreich")
                                    print(f"   Dokumente (Einzelabruf): {single_milestone.get('documents', 'Keine')}")
                                    print(f"   Shared Document IDs: {single_milestone.get('shared_document_ids', 'Keine')}")
                                    
                                    if single_milestone.get('documents'):
                                        docs = single_milestone['documents']
                                        if isinstance(docs, list):
                                            print(f"   📋 {len(docs)} Dokumente im Einzelabruf:")
                                            for i, doc in enumerate(docs):
                                                print(f"      {i+1}. {doc}")
                                        else:
                                            print(f"   📋 Dokumente (Einzelabruf, nicht Liste): {docs}")
                                else:
                                    print(f"   ❌ Einzelabruf fehlgeschlagen: {single_response.status}")
                    else:
                        print(f"❌ Milestones laden fehlgeschlagen: {milestone_response.status}")
                        error_text = await milestone_response.text()
                        print(f"   Fehler: {error_text}")
            else:
                print(f"❌ Login fehlgeschlagen: {response.status}")
                error_text = await response.text()
                print(f"   Fehler: {error_text}")

if __name__ == "__main__":
    asyncio.run(test_bautraeger_api())