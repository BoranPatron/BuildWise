#!/usr/bin/env python3
"""
Test-Skript zum Vergleichen der Bauträger vs Dienstleister Endpoints
"""

import asyncio
import aiohttp
import json

async def test_bautraeger_vs_dienstleister_endpoints():
    """Vergleicht die beiden Endpoints für Bauträger und Dienstleister"""
    
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
            
            bautraeger_token = (await bautraeger_response.json()).get("access_token")
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
            
            dienstleister_token = (await dienstleister_response.json()).get("access_token")
            print(f"✅ Dienstleister Login erfolgreich")
            
            # 3. Teste Bauträger Endpoint (projektbasiert)
            print("\n🏗️ Teste Bauträger Endpoint: /milestones?project_id=7")
            bautraeger_headers = {"Authorization": f"Bearer {bautraeger_token}"}
            
            bautraeger_response = await session.get(
                f"{base_url}/milestones?project_id=7",
                headers=bautraeger_headers
            )
            
            if bautraeger_response.status == 200:
                bautraeger_milestones = await bautraeger_response.json()
                print(f"✅ Bauträger: {len(bautraeger_milestones)} Milestones geladen")
                
                # Analysiere Milestone 1 (das neue Gewerk)
                for milestone in bautraeger_milestones:
                    if milestone.get('id') == 1:
                        print(f"\n📋 Bauträger - Milestone 1: {milestone.get('title')}")
                        documents = milestone.get('documents', [])
                        print(f"    Dokumente: {len(documents)}")
                        print(f"    Dokumente Type: {type(documents)}")
                        print(f"    Dokumente IsArray: {isinstance(documents, list)}")
                        if documents:
                            for i, doc in enumerate(documents):
                                print(f"      {i+1}. {doc.get('title', doc.get('name', 'Unbekannt'))}")
                        else:
                            print(f"    ⚠️ Keine Dokumente")
                        print(f"    🔍 Vollständige Daten: {json.dumps(milestone, indent=2)}")
            else:
                print(f"❌ Bauträger Request fehlgeschlagen: {bautraeger_response.status}")
            
            # 4. Teste Dienstleister Endpoint (alle Milestones)
            print("\n👷 Teste Dienstleister Endpoint: /milestones/all")
            dienstleister_headers = {"Authorization": f"Bearer {dienstleister_token}"}
            
            dienstleister_response = await session.get(
                f"{base_url}/milestones/all",
                headers=dienstleister_headers
            )
            
            if dienstleister_response.status == 200:
                dienstleister_milestones = await dienstleister_response.json()
                print(f"✅ Dienstleister: {len(dienstleister_milestones)} Milestones geladen")
                
                # Analysiere Milestone 1 (das neue Gewerk)
                for milestone in dienstleister_milestones:
                    if milestone.get('id') == 1:
                        print(f"\n📋 Dienstleister - Milestone 1: {milestone.get('title')}")
                        documents = milestone.get('documents', [])
                        print(f"    Dokumente: {len(documents)}")
                        print(f"    Dokumente Type: {type(documents)}")
                        print(f"    Dokumente IsArray: {isinstance(documents, list)}")
                        if documents:
                            for i, doc in enumerate(documents):
                                print(f"      {i+1}. {doc.get('title', doc.get('name', 'Unbekannt'))}")
                        else:
                            print(f"    ⚠️ Keine Dokumente")
                        print(f"    🔍 Vollständige Daten: {json.dumps(milestone, indent=2)}")
            else:
                print(f"❌ Dienstleister Request fehlgeschlagen: {dienstleister_response.status}")
            
            # 5. Vergleiche die Ergebnisse
            print("\n🔍 Vergleich der Endpoints:")
            print(f"Bauträger Endpoint: /milestones?project_id=7")
            print(f"Dienstleister Endpoint: /milestones/all")
            
            if bautraeger_response.status == 200 and dienstleister_response.status == 200:
                bautraeger_data = await bautraeger_response.json()
                dienstleister_data = await dienstleister_response.json()
                
                print(f"\n📊 Anzahl Milestones:")
                print(f"  Bauträger: {len(bautraeger_data)}")
                print(f"  Dienstleister: {len(dienstleister_data)}")
                
                # Finde Milestone 1 in beiden Listen
                bautraeger_milestone_1 = None
                dienstleister_milestone_1 = None
                
                for milestone in bautraeger_data:
                    if milestone.get('id') == 1:
                        bautraeger_milestone_1 = milestone
                        break
                
                for milestone in dienstleister_data:
                    if milestone.get('id') == 1:
                        dienstleister_milestone_1 = milestone
                        break
                
                if bautraeger_milestone_1 and dienstleister_milestone_1:
                    print(f"\n📋 Milestone 1 Vergleich:")
                    print(f"  Bauträger Dokumente: {len(bautraeger_milestone_1.get('documents', []))}")
                    print(f"  Dienstleister Dokumente: {len(dienstleister_milestone_1.get('documents', []))}")
                    
                    if len(bautraeger_milestone_1.get('documents', [])) != len(dienstleister_milestone_1.get('documents', [])):
                        print(f"  ❌ UNTERSCHIED: Verschiedene Anzahl Dokumente!")
                    else:
                        print(f"  ✅ GLEICH: Gleiche Anzahl Dokumente")
                else:
                    print(f"  ⚠️ Milestone 1 nicht in beiden Listen gefunden")
            
        except Exception as e:
            print(f"❌ Fehler: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bautraeger_vs_dienstleister_endpoints()) 