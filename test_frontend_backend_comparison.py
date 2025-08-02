#!/usr/bin/env python3
"""
Test-Skript für den Vergleich der Backend-Endpoints zwischen Dienstleister und Bauträger
"""

import asyncio
import aiohttp
import json

async def test_frontend_backend_comparison():
    """Vergleicht die Backend-Endpoints für Dienstleister und Bauträger"""
    
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
                
                # Analysiere die ersten 3 Milestones
                for i, milestone in enumerate(bautraeger_milestones[:3]):
                    print(f"\n  📋 Bauträger Milestone {i+1}:")
                    print(f"    ID: {milestone.get('id')}")
                    print(f"    Titel: {milestone.get('title')}")
                    print(f"    Kategorie: {milestone.get('category')}")
                    documents = milestone.get('documents', [])
                    print(f"    Dokumente: {len(documents)}")
                    print(f"    Dokumente Type: {type(documents)}")
                    if documents:
                        for j, doc in enumerate(documents):
                            print(f"      {j+1}. {doc.get('title', doc.get('name', 'Unbekannt'))}")
                    else:
                        print(f"      ⚠️ Keine Dokumente")
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
                
                # Analysiere die ersten 3 Milestones
                for i, milestone in enumerate(dienstleister_milestones[:3]):
                    print(f"\n  📋 Dienstleister Milestone {i+1}:")
                    print(f"    ID: {milestone.get('id')}")
                    print(f"    Titel: {milestone.get('title')}")
                    print(f"    Kategorie: {milestone.get('category')}")
                    documents = milestone.get('documents', [])
                    print(f"    Dokumente: {len(documents)}")
                    print(f"    Dokumente Type: {type(documents)}")
                    if documents:
                        for j, doc in enumerate(documents):
                            print(f"      {j+1}. {doc.get('title', doc.get('name', 'Unbekannt'))}")
                    else:
                        print(f"      ⚠️ Keine Dokumente")
            else:
                print(f"❌ Dienstleister Milestones Request fehlgeschlagen")
                error_text = await dienstleister_milestones_response.text()
                print(f"❌ Fehler-Details: {error_text}")
            
            # 5. Vergleich der Datenstrukturen
            print("\n🔍 Vergleich der Datenstrukturen:")
            if bautraeger_milestones_response.status == 200 and dienstleister_milestones_response.status == 200:
                bautraeger_data = await bautraeger_milestones_response.json()
                dienstleister_data = await dienstleister_milestones_response.json()
                
                if bautraeger_data and dienstleister_data:
                    bautraeger_sample = bautraeger_data[0] if bautraeger_data else {}
                    dienstleister_sample = dienstleister_data[0] if dienstleister_data else {}
                    
                    print(f"  📊 Bauträger Sample Keys: {list(bautraeger_sample.keys())}")
                    print(f"  📊 Dienstleister Sample Keys: {list(dienstleister_sample.keys())}")
                    
                    # Prüfe ob beide die gleichen Schlüssel haben
                    bautraeger_keys = set(bautraeger_sample.keys())
                    dienstleister_keys = set(dienstleister_sample.keys())
                    
                    if bautraeger_keys == dienstleister_keys:
                        print(f"  ✅ Beide Endpoints haben die gleiche Datenstruktur")
                    else:
                        print(f"  ❌ Unterschiedliche Datenstrukturen:")
                        print(f"     Nur in Bauträger: {bautraeger_keys - dienstleister_keys}")
                        print(f"     Nur in Dienstleister: {dienstleister_keys - bautraeger_keys}")
            
        except Exception as e:
            print(f"❌ Fehler: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_frontend_backend_comparison()) 