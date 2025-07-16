#!/usr/bin/env python3
"""
Test-Skript für die BuildWise-Fees-API
"""

import requests
import json

def test_buildwise_fees_api():
    """Teste die BuildWise-Fees-API"""
    base_url = "http://localhost:8000"
    
    print("🔍 Teste BuildWise-Fees-API...")
    
    # 1. Teste Backend-Verfügbarkeit
    try:
        response = requests.get(f"{base_url}/api/v1/")
        print(f"✅ Backend erreichbar: {response.status_code}")
    except Exception as e:
        print(f"❌ Backend nicht erreichbar: {e}")
        return
    
    # 2. Teste Login
    login_data = {
        "username": "admin@buildwise.de",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/v1/auth/login", data=login_data)
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
            response = requests.get(f"{base_url}/api/v1/buildwise-fees/", headers=headers)
            print(f"📡 Gebühren-API Status: {response.status_code}")
            
            if response.status_code == 200:
                fees = response.json()
                print(f"✅ Gebühren erfolgreich geladen: {len(fees)} Gebühren")
                for fee in fees:
                    print(f"  - ID: {fee['id']}, Betrag: {fee['total_amount']}€, Status: {fee['status']}")
            else:
                print(f"❌ Gebühren-API Fehler: {response.text}")
            
            # Teste Statistiken
            response = requests.get(f"{base_url}/api/v1/buildwise-fees/statistics", headers=headers)
            print(f"📡 Statistiken-API Status: {response.status_code}")
            
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ Statistiken erfolgreich geladen:")
                print(f"  - Gesamtgebühren: {stats['total_fees']}")
                print(f"  - Gesamtbetrag: {stats['total_amount']}€")
                print(f"  - Bezahlt: {stats['total_paid']}€")
                print(f"  - Offen: {stats['total_open']}€")
            else:
                print(f"❌ Statistiken-API Fehler: {response.text}")
                
        else:
            print(f"❌ Login fehlgeschlagen: {response.text}")
            
    except Exception as e:
        print(f"❌ Fehler beim API-Test: {e}")

if __name__ == "__main__":
    test_buildwise_fees_api() 