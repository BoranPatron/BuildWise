#!/usr/bin/env python3
"""
Skript um die Milestones-API zu testen
"""

import requests
import json

def test_milestones_api():
    """Teste die Milestones-API"""
    base_url = "http://localhost:8000"
    
    print("🔍 Teste Milestones-API...")
    
    try:
        # Teste Backend-Verfügbarkeit
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Backend ist erreichbar")
        else:
            print(f"⚠️ Backend antwortet mit Status {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Backend ist nicht erreichbar - ist es gestartet?")
        print("   Starte das Backend mit: python -m uvicorn app.main:app --reload")
        return
    
    # Teste Login
    print("\n🔐 Teste Login...")
    login_data = {
        'username': 'test-dienstleister@buildwise.de',
        'password': 'test1234'
    }
    
    try:
        response = requests.post(f"{base_url}/api/v1/auth/login", data=login_data)
        if response.status_code == 200:
            print("✅ Login erfolgreich")
            token = response.json()['access_token']
            print(f"🔑 Token erhalten: {token[:20]}...")
            
            # Teste Milestones-API
            print("\n📋 Teste Milestones-API...")
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(f"{base_url}/api/v1/milestones/all", headers=headers)
            
            print(f"📡 API Response Status: {response.status_code}")
            print(f"📡 API Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Milestones geladen: {len(data)} gefunden")
                for milestone in data:
                    print(f"   - {milestone.get('title', 'N/A')} (ID: {milestone.get('id', 'N/A')}, Status: {milestone.get('status', 'N/A')})")
            else:
                print(f"❌ API-Fehler: {response.status_code}")
                print(f"📄 Response: {response.text}")
                
        else:
            print(f"❌ Login fehlgeschlagen: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Fehler beim API-Test: {e}")

if __name__ == "__main__":
    test_milestones_api() 