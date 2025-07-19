#!/usr/bin/env python3
"""
Einfacher Login-Test
"""

import requests
import json

def test_login():
    """Testet den Login"""
    try:
        print("🧪 Teste Admin-Login...")
        
        # Login-Daten
        login_data = {
            "username": "admin@buildwise.de",
            "password": "Admin123!"
        }
        
        # Sende Login-Request
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📡 Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login erfolgreich!")
            print(f"   Token: {data.get('access_token', '')[:20]}...")
            print(f"   User: {data.get('user', {}).get('email', '')}")
            return True
        else:
            print(f"❌ Login fehlgeschlagen")
            return False
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False

if __name__ == "__main__":
    test_login() 