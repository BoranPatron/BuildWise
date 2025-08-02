#!/usr/bin/env python3
"""
Test-Skript für den Datenfluss vom Backend zum Frontend
"""

import asyncio
import aiohttp
import json

async def test_frontend_data_flow():
    """Testet den Datenfluss vom Backend zum Frontend"""
    
    # API-Basis-URL
    base_url = "http://localhost:8000/api/v1"
    
    # Login-Daten für Bauträger
    login_data = {
        "username": "janina.hankus@momentumvisual.de",
        "password": "test123"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. Login
            print("🔐 Login...")
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
            
            # 2. Hole Milestones für Projekt 7 (Bauträger Endpoint)
            print("🏗️ Hole Milestones für Projekt 7...")
            headers = {"Authorization": f"Bearer {access_token}"}
            
            milestones_response = await session.get(
                f"{base_url}/milestones?project_id=7",
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
                    
                    # Dokumente analysieren
                    documents = milestone.get('documents', [])
                    print(f"    Dokumente: {len(documents)}")
                    print(f"    Dokumente Type: {type(documents)}")
                    print(f"    Dokumente IsArray: {isinstance(documents, list)}")
                    
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
                    
                    # Prüfe ob Milestone ID 1 (die mit Dokumenten)
                    if milestone.get('id') == 1:
                        print(f"    🎯 Dies ist Milestone ID 1 mit Dokumenten!")
                        print(f"    🔍 Vollständige Dokumente-Daten: {json.dumps(documents, indent=2)}")
                        
                        # Teste spezifisches Milestone
                        print(f"\n🎯 Teste spezifisches Milestone ID 1...")
                        milestone_response = await session.get(
                            f"{base_url}/milestones/1",
                            headers=headers
                        )
                        
                        if milestone_response.status == 200:
                            milestone_detail = await milestone_response.json()
                            print(f"✅ Milestone Detail geladen")
                            documents_detail = milestone_detail.get('documents', [])
                            print(f"    Dokumente im Detail: {len(documents_detail)}")
                            if documents_detail:
                                for j, doc in enumerate(documents_detail):
                                    print(f"      {j+1}. {doc.get('title', doc.get('name', 'Unbekannt'))}")
                        else:
                            print(f"❌ Milestone Detail nicht gefunden")
                
            else:
                print(f"❌ Milestones Request fehlgeschlagen: {milestones_response.status}")
                error_text = await milestones_response.text()
                print(f"❌ Fehler-Details: {error_text}")
            
        except Exception as e:
            print(f"❌ Fehler: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_frontend_data_flow()) 