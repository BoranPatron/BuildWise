#!/usr/bin/env python3
"""
Test-Skript für Login-Endpunkt
"""

import requests
import json

def test_login():
    print("🔍 Teste Login-Endpunkt...")
    
    # Test-Daten
    login_data = {
        'username': 'admin@buildwise.de',
        'password': 'admin123'
    }
    
    try:
        # Sende POST-Request
        response = requests.post(
            'http://localhost:8000/api/v1/auth/login',
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📡 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login erfolgreich!")
            print(f"🔑 Token: {data.get('access_token', 'N/A')[:20]}...")
            print(f"👤 User: {data.get('user', {}).get('email', 'N/A')}")
            return True
        else:
            print(f"❌ Login fehlgeschlagen: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Verbindungsfehler - Backend läuft nicht")
        return False
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False

if __name__ == "__main__":
    test_login() 