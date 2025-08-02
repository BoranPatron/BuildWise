import requests
import json
from datetime import datetime

def test_frontend_milestone_creation():
    """Simuliert den Frontend-Request für Milestone-Erstellung"""
    
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
        
        # Simuliere Frontend-Request mit FormData (wie im Frontend)
        from requests_toolbelt import MultipartEncoder
        
        milestone_data = MultipartEncoder(
            fields={
                'title': 'Test Gewerk Frontend',
                'description': 'Test Beschreibung vom Frontend',
                'category': 'electrical',
                'priority': 'medium',
                'planned_date': '2024-12-31',
                'notes': 'Test Notizen vom Frontend',
                'requires_inspection': 'false',
                'project_id': '1',
                'document_ids': '[]',
                'shared_document_ids': '[]'
            }
        )
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": milestone_data.content_type
        }
        
        print("🔧 Versuche Milestone mit FormData zu erstellen (Frontend-Style)...")
        create_response = requests.post(
            f"{base_url}/milestones/with-documents", 
            data=milestone_data,
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
            
        # Teste auch den einfachen Endpoint
        print("\n🔧 Teste einfachen Milestone-Endpoint...")
        simple_data = {
            "title": "Test Gewerk Simple",
            "description": "Test Beschreibung Simple",
            "project_id": 1,
            "status": "planned",
            "priority": "medium",
            "planned_date": "2024-12-31",
            "category": "electrical",
            "budget": 5000.0,
            "is_critical": False,
            "notify_on_completion": True,
            "notes": "Test Notizen Simple"
        }
        
        simple_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        simple_response = requests.post(
            f"{base_url}/milestones/", 
            json=simple_data,
            headers=simple_headers
        )
        
        print(f"📊 Simple Response Status: {simple_response.status_code}")
        if simple_response.status_code == 201:
            print("✅ Simple Milestone erfolgreich erstellt!")
        else:
            print(f"❌ Simple Milestone Fehler: {simple_response.text}")
            
    except Exception as e:
        print(f"❌ Fehler beim API-Test: {e}")

if __name__ == "__main__":
    test_frontend_milestone_creation() 