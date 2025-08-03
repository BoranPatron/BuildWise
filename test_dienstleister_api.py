#!/usr/bin/env python3
"""
Test der Dienstleister API mit echten HTTP-Requests
"""
import requests
import json

def test_dienstleister_api():
    print("🔍 Test: Dienstleister API Problem")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api/v1"
    
    # Test 1: Login als Dienstleister
    print("\n1. LOGIN ALS DIENSTLEISTER:")
    login_data = {
        "username": "test-dienstleister@buildwise.de",
        "password": "password"  # Standard-Passwort
    }
    
    try:
        login_response = requests.post(f"{base_url}/auth/login", data=login_data)
        print(f"Login Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get('access_token')
            user_info = login_result.get('user', {})
            
            print(f"✅ Login erfolgreich")
            print(f"   User ID: {user_info.get('id')}")
            print(f"   User Type: {user_info.get('user_type')}")
            print(f"   User Role: {user_info.get('user_role')}")
            print(f"   Token: {token[:20]}...")
            
            # Test 2: Projects API mit Token
            print(f"\n2. PROJECTS API MIT TOKEN:")
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            projects_response = requests.get(f"{base_url}/projects/", headers=headers)
            print(f"Projects Status: {projects_response.status_code}")
            
            if projects_response.status_code == 200:
                projects = projects_response.json()
                print(f"✅ Projects API erfolgreich")
                print(f"   Anzahl Projekte: {len(projects)}")
                
                if len(projects) == 0:
                    print("❌ PROBLEM: Dienstleister sieht 0 Projekte!")
                    print("   Laut Code sollte er ALLE Projekte sehen.")
                else:
                    print("✅ Projekte gefunden:")
                    for project in projects:
                        print(f"     - {project.get('id')}: {project.get('name')}")
            else:
                print(f"❌ Projects API Fehler: {projects_response.text}")
                
        else:
            print(f"❌ Login fehlgeschlagen: {login_response.text}")
            print("Mögliche Passwörter zum Testen:")
            print("  - password")
            print("  - 123456")
            print("  - buildwise")
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
    
    # Test 3: Vergleich mit Bauträger
    print(f"\n3. VERGLEICH MIT BAUTRÄGER:")
    bautraeger_login = {
        "username": "janina.hankus@momentumvisual.de",
        "password": "password"
    }
    
    try:
        bautraeger_response = requests.post(f"{base_url}/auth/login", data=bautraeger_login)
        if bautraeger_response.status_code == 200:
            bautraeger_result = bautraeger_response.json()
            bautraeger_token = bautraeger_result.get('access_token')
            
            bautraeger_headers = {
                'Authorization': f'Bearer {bautraeger_token}',
                'Content-Type': 'application/json'
            }
            
            bautraeger_projects_response = requests.get(f"{base_url}/projects/", headers=bautraeger_headers)
            if bautraeger_projects_response.status_code == 200:
                bautraeger_projects = bautraeger_projects_response.json()
                print(f"✅ Bauträger sieht {len(bautraeger_projects)} Projekte")
                for project in bautraeger_projects:
                    print(f"     - {project.get('id')}: {project.get('name')}")
            
        else:
            print(f"❌ Bauträger Login fehlgeschlagen")
            
    except Exception as e:
        print(f"❌ Bauträger Test Fehler: {e}")

if __name__ == "__main__":
    test_dienstleister_api()