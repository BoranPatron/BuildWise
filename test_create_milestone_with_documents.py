#!/usr/bin/env python3
"""
Test-Skript für die Erstellung eines Milestones mit Dokumenten über die API
"""

import asyncio
import aiohttp
import json
from pathlib import Path

async def test_create_milestone_with_documents():
    """Testet die Erstellung eines Milestones mit Dokumenten über die API"""
    
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
            
            # 2. Erstelle Test-Datei
            test_file_content = b"Test-Dokument Inhalt"
            test_file_path = Path("test_document.txt")
            test_file_path.write_bytes(test_file_content)
            
            # 3. Erstelle Milestone mit Dokument
            print("🏗️ Erstelle Milestone mit Dokument...")
            
            # FormData für Milestone-Erstellung
            from aiohttp import FormData
            form_data = FormData()
            form_data.add_field("title", "Test Gewerk mit Dokument")
            form_data.add_field("description", "Test-Beschreibung")
            form_data.add_field("category", "roofing")
            form_data.add_field("priority", "medium")
            form_data.add_field("planned_date", "2025-08-15")
            form_data.add_field("notes", "Test-Notizen")
            form_data.add_field("requires_inspection", "false")
            form_data.add_field("project_id", "7")
            form_data.add_field("documents", test_file_path.open("rb"), filename="test_document.txt")
            
            # Headers mit Token
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            # API-Call
            milestone_response = await session.post(
                f"{base_url}/milestones/with-documents",
                data=form_data,
                headers=headers
            )
            
            print(f"📊 Milestone-Erstellung Response Status: {milestone_response.status}")
            
            if milestone_response.status == 201:
                milestone_result = await milestone_response.json()
                print(f"✅ Milestone erfolgreich erstellt: ID {milestone_result.get('id')}")
                print(f"📄 Milestone Documents: {milestone_result.get('documents')}")
                
                # 4. Prüfe Milestone über GET-Request
                print("🔍 Prüfe Milestone über GET-Request...")
                get_response = await session.get(
                    f"{base_url}/milestones/{milestone_result.get('id')}",
                    headers=headers
                )
                
                if get_response.status == 200:
                    get_result = await get_response.json()
                    print(f"✅ Milestone abgerufen: ID {get_result.get('id')}")
                    print(f"📄 GET Documents: {get_result.get('documents')}")
                    print(f"📄 GET Documents Type: {type(get_result.get('documents'))}")
                    
                    if get_result.get('documents'):
                        documents = get_result.get('documents')
                        if isinstance(documents, list):
                            print(f"📄 Anzahl Dokumente: {len(documents)}")
                            for i, doc in enumerate(documents):
                                print(f"  {i+1}. {doc.get('title', doc.get('name', 'Unbekannt'))}")
                        else:
                            print(f"⚠️ Documents ist kein Array: {type(documents)}")
                    else:
                        print("⚠️ Keine Dokumente gefunden")
                else:
                    print(f"❌ GET-Request fehlgeschlagen: {get_response.status}")
            else:
                print(f"❌ Milestone-Erstellung fehlgeschlagen: {milestone_response.status}")
                error_text = await milestone_response.text()
                print(f"❌ Fehler-Details: {error_text}")
            
            # 5. Cleanup
            test_file_path.unlink(missing_ok=True)
            
        except Exception as e:
            print(f"❌ Fehler: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_create_milestone_with_documents()) 