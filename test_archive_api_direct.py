#!/usr/bin/env python3
"""
Teste die Archiv-API direkt mit korrekter Authentifizierung
"""

import requests
import json

def test_archive_api_with_auth():
    try:
        # Teste die /milestones/archived API mit einem gültigen Token
        url = "http://localhost:8000/api/v1/milestones/archived"
        
        # Simuliere einen gültigen JWT Token (für Test-Zwecke)
        # In der Realität würde dieser vom Login-Endpoint kommen
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-token"  # Dummy Token für Test
        }
        
        # Füge project_id Parameter hinzu
        params = {
            "project_id": 1
        }
        
        print(f"🔍 Teste API: {url}")
        print(f"📋 Parameter: {params}")
        print(f"🔑 Headers: {headers}")
        
        response = requests.get(url, headers=headers, params=params)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response erfolgreich!")
            print(f"📦 Anzahl archivierter Gewerke: {len(data)}")
            
            if data:
                print("\n🔍 Erstes archiviertes Gewerk:")
                print(json.dumps(data[0], indent=2, ensure_ascii=False))
            else:
                print("⚠️ Keine archivierten Gewerke gefunden")
        else:
            print(f"❌ API Fehler: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Verbindungsfehler: Backend nicht erreichbar")
        print("💡 Stelle sicher, dass das Backend läuft: python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    test_archive_api_with_auth()
