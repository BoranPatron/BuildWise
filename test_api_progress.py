import requests
import json

# Test-Daten
data = {
    "update_type": "comment",
    "message": "Test Kommentar",
    "progress_percentage": 50,
    "parent_id": None,
    "defect_severity": None,
    "is_internal": False
}

# API-Aufruf
url = "http://localhost:8000/api/v1/milestones/1/progress/"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LWRpZW5zdGxlaXN0ZXJAYnVpbGR3aXNlLmRlIiwiZXhwIjoxNzU0MTI0MjAzfQ.example"  # Ersetze mit echtem Token
}

try:
    response = requests.post(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 422:
        print("422 Validation Error Details:")
        try:
            error_details = response.json()
            print(json.dumps(error_details, indent=2))
        except:
            print("Could not parse JSON response")
            
except Exception as e:
    print(f"Error: {e}")