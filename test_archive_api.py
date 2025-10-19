#!/usr/bin/env python3
"""
Teste die Archiv-API direkt
"""

import requests
import json

def test_archive_api():
    try:
        # Teste die /milestones/archived API
        url = "http://localhost:8000/milestones/archived"
        
        # Simuliere einen Bauträger-Request
        headers = {
            "Content-Type": "application/json"
        }
        
        # Füge project_id Parameter hinzu
        params = {
            "project_id": 1  # Angenommen Projekt ID 1
        }
        
        print(f"🔍 Teste API: {url}")
        print(f"📋 Parameter: {params}")
        
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
    test_archive_api()
