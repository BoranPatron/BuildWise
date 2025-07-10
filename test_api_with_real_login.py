import requests
import json

# API-Basis-URL
BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_api():
    print("🔍 Teste API-Verbindung mit echtem Login...")
    
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
            
            # 2. Teste /milestones/all mit echtem Token
            print("\n2️⃣ Teste /milestones/all API...")
            headers = {"Authorization": f"Bearer {token}"}
            
            milestones_response = requests.get(f"{BASE_URL}/milestones/all", headers=headers)
            print(f"Milestones Status: {milestones_response.status_code}")
            
            if milestones_response.status_code == 200:
                milestones_data = milestones_response.json()
                print(f"✅ Milestones API erfolgreich!")
                print(f"Anzahl Milestones: {len(milestones_data)}")
                
                if len(milestones_data) > 0:
                    print("Gefundene Milestones:")
                    for milestone in milestones_data:
                        print(f"  - ID: {milestone.get('id')}, Titel: {milestone.get('title')}, Status: {milestone.get('status')}")
                else:
                    print("❌ Keine Milestones gefunden (leeres Array)")
            else:
                print(f"❌ Milestones API Fehler: {milestones_response.status_code}")
                print(f"Response: {milestones_response.text}")
        else:
            print(f"❌ Login fehlgeschlagen: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            
    except Exception as e:
        print(f"❌ Fehler beim API-Test: {e}")

if __name__ == "__main__":
    test_api() 