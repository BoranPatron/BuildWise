#!/usr/bin/env python3
import requests
import json

def test_notification_apis():
    base_url = "http://localhost:8000/api/v1"
    
    # Test mit User 4 (Bauträger)
    user_id = 4
    
    # Dummy JWT Token (für Test)
    headers = {
        "Authorization": "Bearer dummy-token",
        "Content-Type": "application/json"
    }
    
    print(f"🔍 Teste Notification APIs für User {user_id}...")
    
    try:
        # Test Projects API
        print("\n📋 Teste /projects/")
        projects_response = requests.get(f"{base_url}/projects/", headers=headers)
        print(f"Status: {projects_response.status_code}")
        if projects_response.status_code == 200:
            projects = projects_response.json()
            print(f"Projects: {len(projects)} gefunden")
            print(f"Erste Projekt: {projects[0] if projects else 'None'}")
            
            if projects:
                project_id = projects[0]['id']
                
                # Test Milestones API
                print(f"\n📋 Teste /milestones/?project_id={project_id}")
                milestones_response = requests.get(f"{base_url}/milestones/?project_id={project_id}", headers=headers)
                print(f"Status: {milestones_response.status_code}")
                if milestones_response.status_code == 200:
                    milestones = milestones_response.json()
                    print(f"Milestones: {len(milestones)} gefunden")
                    print(f"Erstes Milestone: {milestones[0] if milestones else 'None'}")
                    
                    if milestones:
                        milestone_id = milestones[0]['id']
                        
                        # Test Progress API
                        print(f"\n📋 Teste /milestones/{milestone_id}/progress/")
                        progress_response = requests.get(f"{base_url}/milestones/{milestone_id}/progress/", headers=headers)
                        print(f"Status: {progress_response.status_code}")
                        if progress_response.status_code == 200:
                            progress_updates = progress_response.json()
                            print(f"Progress Updates: {len(progress_updates)} gefunden")
                            for update in progress_updates[:3]:  # Erste 3
                                print(f"  Update {update['id']}: User {update['user_id']}, Message: \"{update['message'][:50]}...\"")
                        else:
                            print(f"❌ Progress API Fehler: {progress_response.text}")
                else:
                    print(f"❌ Milestones API Fehler: {milestones_response.text}")
        else:
            print(f"❌ Projects API Fehler: {projects_response.text}")
            
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    test_notification_apis()