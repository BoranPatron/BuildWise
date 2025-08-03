#!/usr/bin/env python3
import requests
import json

def test_projects_api():
    base_url = "http://localhost:8000/api/v1"
    
    # Test für verschiedene User
    test_users = [
        (4, "Bauträger (PRIVATE)"),
        (6, "Dienstleister (SERVICE_PROVIDER)")
    ]
    
    for user_id, description in test_users:
        print(f"\n🔍 Teste /projects/ für User {user_id} ({description})")
        
        # Erstelle einen einfachen Test-Token (nicht sicher, nur für Test)
        import jwt
        token_payload = {
            'user_id': user_id,
            'sub': f'test{user_id}@test.com',
            'exp': 9999999999  # Weit in der Zukunft
        }
        token = jwt.encode(token_payload, 'your-secret-key', algorithm='HS256')
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(f"{base_url}/projects/", headers=headers)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                projects = response.json()
                print(f"✅ {len(projects)} Projekte erhalten")
                for project in projects:
                    print(f"  - Projekt {project['id']}: {project['name']} (Besitzer: {project['owner_id']})")
            else:
                print(f"❌ Fehler: {response.text}")
                
        except Exception as e:
            print(f"❌ Network Error: {e}")

if __name__ == "__main__":
    test_projects_api()