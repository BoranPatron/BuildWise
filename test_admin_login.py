#!/usr/bin/env python3
"""
Test-Script für Admin-Login
"""

import requests
import json

def test_admin_login():
    """Testet den Admin-Login"""
    
    url = "http://localhost:8000/auth/login"
    data = {
        "username": "admin@buildwise.de",
        "password": "Admin123!"
    }
    
    try:
        print("🔍 Teste Admin-Login...")
        response = requests.post(url, data=data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Login erfolgreich!")
            token_data = response.json()
            print(f"Token: {token_data.get('access_token', 'N/A')[:50]}...")
        else:
            print("❌ Login fehlgeschlagen!")
            
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    test_admin_login() 