#!/usr/bin/env python3
"""
Skript zum Überprüfen aller Milestones und ihrer Dokumente
"""

import asyncio
import aiohttp
import json

async def check_all_milestones_documents():
    """Überprüft alle Milestones und ihre Dokumente"""
    
    # API-Basis-URL
    base_url = "http://localhost:8000/api/v1"
    
    # Login-Daten für Dienstleister
    login_data = {
        "username": "test@buildwise.de",
        "password": "test123"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. Login
            print("🔐 Dienstleister Login...")
            login_response = await session.post(
                f"{base_url}/auth/login",
                data=login_data
            )
            
            if login_response.status != 200:
                print(f"❌ Login fehlgeschlagen: {login_response.status}")
                return
            
            login_result = await login_response.json()
            access_token = login_result.get("access_token")
            print(f"✅ Login erfolgreich, Token erhalten")
            
            # 2. Hole alle Milestones
            print("👷 Hole alle Milestones...")
            headers = {"Authorization": f"Bearer {access_token}"}
            
            milestones_response = await session.get(
                f"{base_url}/milestones/all",
                headers=headers
            )
            
            if milestones_response.status == 200:
                milestones = await milestones_response.json()
                print(f"✅ {len(milestones)} Milestones geladen")
                
                # Analysiere jedes Milestone
                for i, milestone in enumerate(milestones):
                    print(f"\n📋 Milestone {i+1}: {milestone.get('title')} (ID: {milestone.get('id')})")
                    print(f"    Kategorie: {milestone.get('category')}")
                    print(f"    Status: {milestone.get('status')}")
                    print(f"    Projekt ID: {milestone.get('project_id')}")
                    
                    # Dokumente analysieren
                    documents = milestone.get('documents', [])
                    print(f"    Dokumente: {len(documents)}")
                    
                    if documents:
                        print(f"    📄 Dokumente Details:")
                        for j, doc in enumerate(documents):
                            print(f"      {j+1}. {doc.get('title', doc.get('name', 'Unbekannt'))}")
                            print(f"         Type: {doc.get('type', doc.get('mime_type', 'Unbekannt'))}")
                            print(f"         Size: {doc.get('size', doc.get('file_size', 'Unbekannt'))}")
                            print(f"         URL: {doc.get('url', doc.get('file_path', 'Unbekannt'))}")
                            print(f"         ID: {doc.get('id', 'Unbekannt')}")
                    else:
                        print(f"    ⚠️ Keine Dokumente")
                
                # 3. Teste spezifische Milestones
                print(f"\n🎯 Teste spezifische Milestones...")
                for milestone_id in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
                    print(f"\n📋 Teste Milestone ID {milestone_id}:")
                    
                    milestone_response = await session.get(
                        f"{base_url}/milestones/{milestone_id}",
                        headers=headers
                    )
                    
                    if milestone_response.status == 200:
                        milestone = await milestone_response.json()
                        documents = milestone.get('documents', [])
                        print(f"  ✅ Milestone {milestone_id}: {milestone.get('title')}")
                        print(f"    Dokumente: {len(documents)}")
                        if documents:
                            for j, doc in enumerate(documents):
                                print(f"      {j+1}. {doc.get('title', doc.get('name', 'Unbekannt'))}")
                    else:
                        print(f"  ❌ Milestone {milestone_id} nicht gefunden")
            
            else:
                print(f"❌ Milestones Request fehlgeschlagen: {milestones_response.status}")
                error_text = await milestones_response.text()
                print(f"❌ Fehler-Details: {error_text}")
            
        except Exception as e:
            print(f"❌ Fehler: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_all_milestones_documents()) 