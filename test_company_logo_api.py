#!/usr/bin/env python3
"""
Test für den neuen Company Logo API Endpoint
"""

import requests
import json

# Test-Konfiguration
BASE_URL = "http://localhost:8000"
USER_ID = 2

def test_company_logo_endpoint():
    """Testet den neuen /users/{user_id}/company-logo Endpoint"""
    
    print("🧪 Teste Company Logo API Endpoint")
    print("=" * 50)
    
    # 1. Login um Token zu erhalten
    print("1️⃣ Login...")
    login_data = {
        "username": "s.schellworth@valueon.ch",
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
        if response.status_code != 200:
            print(f"❌ Login fehlgeschlagen: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        token = response.json()["access_token"]
        print("✅ Login erfolgreich")
        
        # 2. Teste Company Logo Endpoint
        print(f"\n2️⃣ Teste Company Logo Endpoint für User ID {USER_ID}...")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{BASE_URL}/api/v1/users/{USER_ID}/company-logo", headers=headers)
        
        if response.status_code == 200:
            logo_data = response.json()
            print("✅ Company Logo Endpoint erfolgreich!")
            print(f"📊 Response: {json.dumps(logo_data, indent=2)}")
            
            # 3. Validiere Response-Struktur
            required_fields = ["user_id", "company_name", "company_logo", "company_logo_advertising_consent"]
            missing_fields = [field for field in required_fields if field not in logo_data]
            
            if missing_fields:
                print(f"⚠️ Fehlende Felder: {missing_fields}")
            else:
                print("✅ Alle erforderlichen Felder vorhanden")
                
        else:
            print(f"❌ Company Logo Endpoint fehlgeschlagen: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Fehler beim Testen: {e}")

if __name__ == "__main__":
    test_company_logo_endpoint()
