#!/usr/bin/env python3
"""
Einfaches Test-Skript für Backend-Verbindung
"""

import requests
import json

def test_backend():
    print("🔍 Teste Backend-Verbindung...")
    
    try:
        # Test 1: Health Check
        print("\n1. Health Check:")
        response = requests.get('http://localhost:8000/api/v1/')
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Test 2: Login-Endpunkt
        print("\n2. Login-Endpunkt Test:")
        login_data = {
            'username': 'admin@buildwise.de',
            'password': 'admin123'
        }
        
        response = requests.post(
            'http://localhost:8000/api/v1/auth/login',
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Login erfolgreich!")
            print(f"Token: {data.get('access_token', 'N/A')[:20]}...")
            print(f"User: {data.get('user', {}).get('email', 'N/A')}")
        else:
            print("❌ Login fehlgeschlagen")
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend nicht erreichbar - ist es gestartet?")
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    test_backend() 