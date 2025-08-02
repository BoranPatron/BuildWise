#!/usr/bin/env python3
"""
Testet die Bauträger-API für Dokumente
"""

import requests
import json

def test_bautraeger_documents():
    print("🔍 Teste Bauträger-API für Dokumente...")
    
    # Bauträger Login
    login_data = {
        "email": "janina.hankus@momentumvisual.de",
        "password": "password"
    }
    
    base_url = "http://localhost:8000/api/v1"
    
    try:
        # Login
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"❌ Login fehlgeschlagen: {response.status_code}")
            return
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        print("✅ Bauträger Login erfolgreich")
        
        # Teste Milestone 1
        print("\n📋 Teste Milestone 1 (TEST_Bodenlegen):")
        response = requests.get(f"{base_url}/milestones/1", headers=headers)
        if response.status_code == 200:
            milestone = response.json()
            print(f"✅ Milestone geladen: {milestone['title']}")
            print(f"📄 Documents: {milestone.get('documents', [])}")
            print(f"📄 Documents Anzahl: {len(milestone.get('documents', []))}")
        else:
            print(f"❌ Fehler beim Laden von Milestone 1: {response.status_code}")
        
        # Teste Milestone 2
        print("\n📋 Teste Milestone 2 (tet):")
        response = requests.get(f"{base_url}/milestones/2", headers=headers)
        if response.status_code == 200:
            milestone = response.json()
            print(f"✅ Milestone geladen: {milestone['title']}")
            print(f"📄 Documents: {milestone.get('documents', [])}")
            print(f"📄 Documents Anzahl: {len(milestone.get('documents', []))}")
        else:
            print(f"❌ Fehler beim Laden von Milestone 2: {response.status_code}")
        
        # Teste Geo-Suche für Bauträger
        print("\n🔍 Teste Geo-Suche für Bauträger:")
        geo_data = {
            "latitude": 47.3769,
            "longitude": 8.5417,
            "radius_km": 50,
            "limit": 10
        }
        
        response = requests.post(f"{base_url}/geo/search-trades", json=geo_data, headers=headers)
        if response.status_code == 200:
            trades = response.json()
            print(f"✅ {len(trades)} Trades gefunden")
            
            for trade in trades:
                print(f"  📋 Trade {trade['id']}: {trade['title']}")
                print(f"    📄 Documents: {len(trade.get('documents', []))}")
                if trade.get('documents'):
                    for doc in trade['documents']:
                        print(f"      📄 {doc.get('name', 'Unbekannt')}")
        else:
            print(f"❌ Fehler bei Geo-Suche: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    test_bautraeger_documents() 