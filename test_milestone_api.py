import requests
import json
from datetime import datetime

def test_milestone_api():
    """Testet den Milestone-API-Endpoint"""
    
    # API Base URL
    base_url = "http://localhost:8000/api/v1"
    
    # Login um Token zu bekommen
    login_data = {
        "username": "test@buildwise.de",
        "password": "test123"
    }
    
    try:
        # Login
        print("🔧 Versuche Login...")
        login_response = requests.post(f"{base_url}/auth/login", data=login_data)
        
        if login_response.status_code != 200:
            print(f"❌ Login fehlgeschlagen: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return
        
        token = login_response.json()["access_token"]
        print("✅ Login erfolgreich")
        
        # Teste Milestone erstellen
        milestone_data = {
            "title": "Test Gewerk API",
            "description": "Test Beschreibung via API",
            "project_id": 1,
            "status": "planned",
            "priority": "medium",
            "planned_date": "2024-12-31",
            "category": "electrical",
            "budget": 5000.0,
            "is_critical": False,
            "notify_on_completion": True,
            "notes": "Test Notizen"
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        print("🔧 Versuche Milestone zu erstellen...")
        create_response = requests.post(
            f"{base_url}/milestones/", 
            json=milestone_data,
            headers=headers
        )
        
        print(f"📊 Response Status: {create_response.status_code}")
        print(f"📊 Response Headers: {dict(create_response.headers)}")
        print(f"📊 Response Body: {create_response.text}")
        
        if create_response.status_code == 201:
            print("✅ Milestone erfolgreich erstellt!")
            milestone = create_response.json()
            print(f"📋 Erstelltes Milestone: ID={milestone.get('id')}, Titel={milestone.get('title')}")
        else:
            print(f"❌ Fehler beim Erstellen des Milestones: {create_response.status_code}")
            
        # Teste Milestones abrufen
        print("\n🔧 Versuche Milestones abzurufen...")
        list_response = requests.get(
            f"{base_url}/milestones/?project_id=1",
            headers=headers
        )
        
        print(f"📊 List Response Status: {list_response.status_code}")
        if list_response.status_code == 200:
            milestones = list_response.json()
            print(f"📋 Anzahl Milestones: {len(milestones)}")
            for milestone in milestones:
                print(f"  - ID: {milestone.get('id')}, Titel: {milestone.get('title')}, Status: {milestone.get('status')}")
        else:
            print(f"❌ Fehler beim Abrufen der Milestones: {list_response.status_code}")
            print(f"Response: {list_response.text}")
            
    except Exception as e:
        print(f"❌ Fehler beim API-Test: {e}")

if __name__ == "__main__":
    test_milestone_api() 