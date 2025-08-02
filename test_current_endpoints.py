#!/usr/bin/env python3
"""
Einfaches Test-Skript für die aktuellen Endpoint-Daten
"""

import asyncio
import aiohttp
import json

async def test_current_endpoints():
    """Testet die aktuellen Endpoint-Daten"""
    
    base_url = "http://localhost:8000/api/v1"
    
    # Login-Daten
    bautraeger_login = {
        "username": "janina.hankus@momentumvisual.de",
        "password": "test123"
    }
    
    dienstleister_login = {
        "username": "test@buildwise.de",
        "password": "test123"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # Bauträger Login
            print("🔐 Bauträger Login...")
            bautraeger_response = await session.post(
                f"{base_url}/auth/login",
                data=bautraeger_login
            )
            bautraeger_token = (await bautraeger_response.json()).get("access_token")
            
            # Dienstleister Login
            print("🔐 Dienstleister Login...")
            dienstleister_response = await session.post(
                f"{base_url}/auth/login",
                data=dienstleister_login
            )
            dienstleister_token = (await dienstleister_response.json()).get("access_token")
            
            # Teste beide Endpoints
            print("\n🏗️ Bauträger Endpoint: /milestones?project_id=7")
            bautraeger_data = await session.get(
                f"{base_url}/milestones?project_id=7",
                headers={"Authorization": f"Bearer {bautraeger_token}"}
            )
            
            print("👷 Dienstleister Endpoint: /milestones/all")
            dienstleister_data = await session.get(
                f"{base_url}/milestones/all",
                headers={"Authorization": f"Bearer {dienstleister_token}"}
            )
            
            # Vergleiche die Ergebnisse
            if bautraeger_data.status == 200 and dienstleister_data.status == 200:
                bautraeger_milestones = await bautraeger_data.json()
                dienstleister_milestones = await dienstleister_data.json()
                
                print(f"\n📊 Vergleich:")
                print(f"Bauträger Milestones: {len(bautraeger_milestones)}")
                print(f"Dienstleister Milestones: {len(dienstleister_milestones)}")
                
                # Finde Milestone 1 in beiden Listen
                bautraeger_m1 = None
                dienstleister_m1 = None
                
                for m in bautraeger_milestones:
                    if m.get('id') == 1:
                        bautraeger_m1 = m
                        break
                
                for m in dienstleister_milestones:
                    if m.get('id') == 1:
                        dienstleister_m1 = m
                        break
                
                if bautraeger_m1 and dienstleister_m1:
                    print(f"\n📋 Milestone 1 Vergleich:")
                    print(f"Bauträger Dokumente: {len(bautraeger_m1.get('documents', []))}")
                    print(f"Dienstleister Dokumente: {len(dienstleister_m1.get('documents', []))}")
                    
                    bautraeger_docs = bautraeger_m1.get('documents', [])
                    dienstleister_docs = dienstleister_m1.get('documents', [])
                    
                    if len(bautraeger_docs) != len(dienstleister_docs):
                        print(f"❌ UNTERSCHIED: Verschiedene Anzahl Dokumente!")
                    else:
                        print(f"✅ GLEICH: Gleiche Anzahl Dokumente")
                    
                    # Zeige die ersten 3 Dokumente von beiden
                    print(f"\n📄 Bauträger Dokumente (erste 3):")
                    for i, doc in enumerate(bautraeger_docs[:3]):
                        print(f"  {i+1}. {doc.get('title', doc.get('name', 'Unbekannt'))}")
                    
                    print(f"\n📄 Dienstleister Dokumente (erste 3):")
                    for i, doc in enumerate(dienstleister_docs[:3]):
                        print(f"  {i+1}. {doc.get('title', doc.get('name', 'Unbekannt'))}")
                else:
                    print("⚠️ Milestone 1 nicht in beiden Listen gefunden")
            else:
                print(f"❌ Request fehlgeschlagen: Bauträger {bautraeger_data.status}, Dienstleister {dienstleister_data.status}")
                
        except Exception as e:
            print(f"❌ Fehler: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_current_endpoints()) 