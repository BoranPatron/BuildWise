import requests
import json

# Test der /milestones/all API
def test_milestones_all_api():
    base_url = "http://localhost:8000/api/v1"
    
    # Service Provider Token (User 3: s.schellworth@valueon.ch)
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzLnNjaGVsbHdvcnRoQHZhbHVlb24uY2giLCJ1c2VyX2lkIjozLCJleHAiOjE3NTk1NzI2MzV9.placeholder"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        print("Teste /milestones/all API...")
        response = requests.get(f"{base_url}/milestones/all", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"API erfolgreich: {len(data)} Milestones")
            
            for milestone in data:
                print(f"Milestone {milestone['id']}: {milestone['title']}")
                print(f"   - has_unread_messages_bautraeger: {milestone.get('has_unread_messages_bautraeger', 'MISSING')}")
                print(f"   - has_unread_messages_dienstleister: {milestone.get('has_unread_messages_dienstleister', 'MISSING')}")
                print(f"   - has_unread_messages: {milestone.get('has_unread_messages', 'MISSING')}")
                print()
        else:
            print(f"API Fehler: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Fehler: {e}")

if __name__ == "__main__":
    test_milestones_all_api()
