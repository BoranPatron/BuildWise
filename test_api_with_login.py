import requests
import json

# API-Basis-URL
BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_api():
    print("🔍 Teste API-Verbindung...")
    
    # 1. Login mit Dienstleister-Account
    print("\n1️⃣ Login mit Dienstleister-Account...")
    login_data = {
        "username": "test-dienstleister@buildwise.de",
        "password": "test1234"
    }
    
    try:
        login_response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
        print(f"Login Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get("access_token")
            print(f"✅ Login erfolgreich, Token erhalten: {token[:20]}...")
            
            # 2. Teste Milestones-API mit Token
            print("\n2️⃣ Teste Milestones-API...")
            headers = {"Authorization": f"Bearer {token}"}
            
            milestones_response = requests.get(f"{BASE_URL}/milestones/all", headers=headers)
            print(f"Milestones Status: {milestones_response.status_code}")
            
            if milestones_response.status_code == 200:
                milestones_data = milestones_response.json()
                print(f"✅ Milestones geladen: {len(milestones_data)} Gewerke gefunden")
                
                for milestone in milestones_data:
                    print(f"  - {milestone.get('title', 'N/A')} (Status: {milestone.get('status', 'N/A')})")
            else:
                print(f"❌ Milestones-API Fehler: {milestones_response.text}")
                
        else:
            print(f"❌ Login fehlgeschlagen: {login_response.text}")
            
    except Exception as e:
        print(f"❌ Fehler beim API-Test: {e}")

if __name__ == "__main__":
    test_api() 