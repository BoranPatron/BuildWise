#!/usr/bin/env python3
"""
Test-Skript für den Vergleich der Dokumentenanzeige zwischen Dienstleister und Bauträger
"""

import asyncio
import aiohttp
import json

async def test_dienstleister_vs_bautraeger_documents():
    """Vergleicht die Dokumentenanzeige zwischen Dienstleister und Bauträger"""
    
    # API-Basis-URL
    base_url = "http://localhost:8000/api/v1"
    
    # Login-Daten für Bauträger
    bautraeger_login = {
        "username": "janina.hankus@momentumvisual.de",
        "password": "test123"
    }
    
    # Login-Daten für Dienstleister
    dienstleister_login = {
        "username": "test@buildwise.de",
        "password": "test123"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. Bauträger Login
            print("🔐 Bauträger Login...")
            bautraeger_response = await session.post(
                f"{base_url}/auth/login",
                data=bautraeger_login
            )
            
            if bautraeger_response.status != 200:
                print(f"❌ Bauträger Login fehlgeschlagen: {bautraeger_response.status}")
                return
            
            bautraeger_result = await bautraeger_response.json()
            bautraeger_token = bautraeger_result.get("access_token")
            print(f"✅ Bauträger Login erfolgreich")
            
            # 2. Dienstleister Login
            print("🔐 Dienstleister Login...")
            dienstleister_response = await session.post(
                f"{base_url}/auth/login",
                data=dienstleister_login
            )
            
            if dienstleister_response.status != 200:
                print(f"❌ Dienstleister Login fehlgeschlagen: {dienstleister_response.status}")
                return
            
            dienstleister_result = await dienstleister_response.json()
            dienstleister_token = dienstleister_result.get("access_token")
            print(f"✅ Dienstleister Login erfolgreich")
            
            # 3. Teste Bauträger Endpoint (/milestones?project_id=7)
            print("\n🏗️ Teste Bauträger Endpoint...")
            bautraeger_headers = {"Authorization": f"Bearer {bautraeger_token}"}
            bautraeger_milestones_response = await session.get(
                f"{base_url}/milestones?project_id=7",
                headers=bautraeger_headers
            )
            
            print(f"📊 Bauträger Response Status: {bautraeger_milestones_response.status}")
            
            if bautraeger_milestones_response.status == 200:
                bautraeger_milestones = await bautraeger_milestones_response.json()
                print(f"✅ Bauträger Milestones geladen: {len(bautraeger_milestones)} Milestones")
                
                # Analysiere Milestones mit Dokumenten
                for i, milestone in enumerate(bautraeger_milestones):
                    documents = milestone.get('documents', [])
                    if documents:
                        print(f"\n  📋 Bauträger Milestone {i+1}: {milestone.get('title')} (ID: {milestone.get('id')})")
                        print(f"    Dokumente: {len(documents)}")
                        print(f"    Dokumente Type: {type(documents)}")
                        print(f"    Dokumente IsArray: {isinstance(documents, list)}")
                        for j, doc in enumerate(documents):
                            print(f"      {j+1}. {doc.get('title', doc.get('name', 'Unbekannt'))}")
                            print(f"         Type: {doc.get('type', doc.get('mime_type', 'Unbekannt'))}")
                            print(f"         Size: {doc.get('size', doc.get('file_size', 'Unbekannt'))}")
                            print(f"         URL: {doc.get('url', doc.get('file_path', 'Unbekannt'))}")
            else:
                print(f"❌ Bauträger Milestones Request fehlgeschlagen")
                error_text = await bautraeger_milestones_response.text()
                print(f"❌ Fehler-Details: {error_text}")
            
            # 4. Teste Dienstleister Endpoint (/milestones/all)
            print("\n👷 Teste Dienstleister Endpoint...")
            dienstleister_headers = {"Authorization": f"Bearer {dienstleister_token}"}
            dienstleister_milestones_response = await session.get(
                f"{base_url}/milestones/all",
                headers=dienstleister_headers
            )
            
            print(f"📊 Dienstleister Response Status: {dienstleister_milestones_response.status}")
            
            if dienstleister_milestones_response.status == 200:
                dienstleister_milestones = await dienstleister_milestones_response.json()
                print(f"✅ Dienstleister Milestones geladen: {len(dienstleister_milestones)} Milestones")
                
                # Analysiere Milestones mit Dokumenten
                for i, milestone in enumerate(dienstleister_milestones):
                    documents = milestone.get('documents', [])
                    if documents:
                        print(f"\n  📋 Dienstleister Milestone {i+1}: {milestone.get('title')} (ID: {milestone.get('id')})")
                        print(f"    Dokumente: {len(documents)}")
                        print(f"    Dokumente Type: {type(documents)}")
                        print(f"    Dokumente IsArray: {isinstance(documents, list)}")
                        for j, doc in enumerate(documents):
                            print(f"      {j+1}. {doc.get('title', doc.get('name', 'Unbekannt'))}")
                            print(f"         Type: {doc.get('type', doc.get('mime_type', 'Unbekannt'))}")
                            print(f"         Size: {doc.get('size', doc.get('file_size', 'Unbekannt'))}")
                            print(f"         URL: {doc.get('url', doc.get('file_path', 'Unbekannt'))}")
            else:
                print(f"❌ Dienstleister Milestones Request fehlgeschlagen")
                error_text = await dienstleister_milestones_response.text()
                print(f"❌ Fehler-Details: {error_text}")
            
            # 5. Teste spezifisches Milestone mit Dokumenten
            print(f"\n🎯 Teste spezifisches Milestone mit Dokumenten...")
            for milestone_id in [1, 4, 5]:  # Teste verschiedene Milestones
                print(f"\n📋 Teste Milestone ID {milestone_id}:")
                
                # Bauträger
                bautraeger_milestone_response = await session.get(
                    f"{base_url}/milestones/{milestone_id}",
                    headers=bautraeger_headers
                )
                
                if bautraeger_milestone_response.status == 200:
                    bautraeger_milestone = await bautraeger_milestone_response.json()
                    documents = bautraeger_milestone.get('documents', [])
                    print(f"  🏗️ Bauträger - Dokumente: {len(documents)}")
                    if documents:
                        for j, doc in enumerate(documents):
                            print(f"    {j+1}. {doc.get('title', doc.get('name', 'Unbekannt'))}")
                else:
                    print(f"  ❌ Bauträger - Milestone {milestone_id} nicht gefunden")
                
                # Dienstleister
                dienstleister_milestone_response = await session.get(
                    f"{base_url}/milestones/{milestone_id}",
                    headers=dienstleister_headers
                )
                
                if dienstleister_milestone_response.status == 200:
                    dienstleister_milestone = await dienstleister_milestone_response.json()
                    documents = dienstleister_milestone.get('documents', [])
                    print(f"  👷 Dienstleister - Dokumente: {len(documents)}")
                    if documents:
                        for j, doc in enumerate(documents):
                            print(f"    {j+1}. {doc.get('title', doc.get('name', 'Unbekannt'))}")
                else:
                    print(f"  ❌ Dienstleister - Milestone {milestone_id} nicht gefunden")
            
        except Exception as e:
            print(f"❌ Fehler: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_dienstleister_vs_bautraeger_documents()) 