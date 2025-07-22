#!/usr/bin/env python3
"""
Test-Skript für BuildWise Fees API mit Authentifizierung
"""

import requests
import json
from datetime import datetime

def test_api_with_auth():
    """Testet die BuildWise Fees API mit Authentifizierung."""
    
    base_url = "http://localhost:8000/api/v1"
    
    print("🔍 Teste BuildWise Fees API mit Authentifizierung...")
    
    # 1. Teste Backend-Verfügbarkeit
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ Backend erreichbar: {response.status_code}")
    except Exception as e:
        print(f"❌ Backend nicht erreichbar: {e}")
        return
    
    # 2. Teste Login
    login_data = {
        "username": "admin@buildwise.de",
        "password": "Admin123!"
    }
    
    try:
        response = requests.post(f"{base_url}/auth/login", data=login_data)
        print(f"📡 Login Status: {response.status_code}")
        
        if response.status_code == 200:
            login_response = response.json()
            token = login_response.get('access_token')
            print(f"✅ Login erfolgreich, Token erhalten: {token[:20]}...")
            
            # 3. Teste BuildWise-Fees-API mit Token
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Teste Gebühren laden
            print("\n🔍 Teste BuildWise Fees API...")
            response = requests.get(f"{base_url}/buildwise-fees/", headers=headers)
            print(f"📡 Gebühren-API Status: {response.status_code}")
            
            if response.status_code == 200:
                fees = response.json()
                print(f"✅ Gebühren erfolgreich geladen: {len(fees)} Gebühren")
                for fee in fees[:3]:  # Zeige nur die ersten 3
                    print(f"  - ID: {fee.get('id')}, Betrag: {fee.get('fee_amount')}€, Status: {fee.get('status')}")
            else:
                print(f"❌ Gebühren-API Fehler: {response.text}")
            
            # Teste Statistiken
            print("\n📊 Teste Statistiken API...")
            response = requests.get(f"{base_url}/buildwise-fees/statistics", headers=headers)
            print(f"📡 Statistiken-API Status: {response.status_code}")
            
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ Statistiken erfolgreich geladen:")
                print(f"  - Gesamtgebühren: {stats.get('total_fees')}")
                print(f"  - Gesamtbetrag: {stats.get('total_amount')}€")
                print(f"  - Bezahlt: {stats.get('total_paid')}€")
                print(f"  - Offen: {stats.get('total_open')}€")
            else:
                print(f"❌ Statistiken-API Fehler: {response.text}")
                
        else:
            print(f"❌ Login fehlgeschlagen: {response.text}")
            
    except Exception as e:
        print(f"❌ Fehler beim API-Test: {e}")

if __name__ == "__main__":
    test_api_with_auth() 