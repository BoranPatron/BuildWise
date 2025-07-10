#!/usr/bin/env python3
"""
Skript um die Backend-Verbindung und den Login zu testen
"""

import requests
import json

def test_backend_connection():
    """Teste die Backend-Verbindung und den Login"""
    base_url = "http://localhost:8000"
    
    print("🔍 Teste Backend-Verbindung...")
    
    try:
        # Teste Backend-Verfügbarkeit
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Backend ist erreichbar")
        else:
            print(f"⚠️ Backend antwortet mit Status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Backend ist nicht erreichbar - ist es gestartet?")
        print("   Starte das Backend mit: python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Fehler beim Verbindungstest: {e}")
        return False
    
    print("\n🔍 Teste Login...")
    
    try:
        # Teste Login mit Dienstleister
        login_data = {
            "username": "test-dienstleister@buildwise.de",
            "password": "test1234"
        }
        
        response = requests.post(
            f"{base_url}/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        print(f"📡 Login-Response Status: {response.status_code}")
        print(f"📡 Login-Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login erfolgreich!")
            print(f"   Token: {data.get('access_token', 'N/A')[:20]}...")
            print(f"   User: {data.get('user', {}).get('email', 'N/A')}")
            print(f"   User Type: {data.get('user', {}).get('user_type', 'N/A')}")
            return True
        else:
            print(f"❌ Login fehlgeschlagen mit Status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Fehler beim Login-Test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starte Backend-Verbindungstest...")
    success = test_backend_connection()
    
    if success:
        print("\n✅ Backend-Test erfolgreich - Frontend sollte funktionieren")
    else:
        print("\n❌ Backend-Test fehlgeschlagen - bitte Backend starten") 