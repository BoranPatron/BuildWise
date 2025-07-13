import requests
import json

def test_cost_positions_api():
    # Backend-URL
    base_url = "https://buildwise-backend.onrender.com"
    
    # Test-Token (ersetze durch echten Token)
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBidWlsZHdpc2UuZGUiLCJleHAiOjE3MzU2NzIwMDB9.example"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Teste verschiedene Endpunkte
    endpoints = [
        "/api/v1/cost-positions/?project_id=4&accepted_quotes_only=true",
        "/api/v1/cost-positions/?project_id=4",
        "/api/v1/cost-positions/project/4/statistics?accepted_quotes_only=true"
    ]
    
    for endpoint in endpoints:
        print(f"\n🔍 Teste: {endpoint}")
        try:
            response = requests.get(f"{base_url}{endpoint}", headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
        except Exception as e:
            print(f"Fehler: {e}")

if __name__ == "__main__":
    test_cost_positions_api() 