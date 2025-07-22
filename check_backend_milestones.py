#!/usr/bin/env python3
"""
Überprüft die Milestones im Backend
"""

import requests
import json

def check_backend_milestones():
    """Überprüft die Milestones im Backend"""
    print("🔍 BACKEND MILESTONES ÜBERPRÜFUNG")
    print("=" * 40)
    
    base_url = "http://localhost:8000"
    
    # Admin-Token
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBidWlsZHdpc2UuZGUiLCJleHAiOjE3NTI5NDY2OTh9.QybsYBe-4RUGdICzDAplsIzxmuaDGHTLMp5_k3YfKNA",
        "Content-Type": "application/json"
    }
    
    try:
        # 1. Teste /api/v1/milestones/all
        print("\n📊 TESTE /api/v1/milestones/all:")
        response = requests.get(f"{base_url}/api/v1/milestones/all", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            milestones = response.json()
            print(f"   Milestones gefunden: {len(milestones)}")
            for i, milestone in enumerate(milestones):
                print(f"   - {i+1}. {milestone.get('title', 'N/A')} (ID: {milestone.get('id', 'N/A')}, Status: {milestone.get('status', 'N/A')})")
        else:
            print(f"   ❌ Fehler: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Fehler beim Test: {e}")
    
    try:
        # 2. Teste /api/v1/milestones?project_id=1
        print("\n📊 TESTE /api/v1/milestones?project_id=1:")
        response = requests.get(f"{base_url}/api/v1/milestones?project_id=1", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            milestones = response.json()
            print(f"   Milestones gefunden: {len(milestones)}")
            for i, milestone in enumerate(milestones):
                print(f"   - {i+1}. {milestone.get('title', 'N/A')} (ID: {milestone.get('id', 'N/A')}, Status: {milestone.get('status', 'N/A')})")
        else:
            print(f"   ❌ Fehler: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Fehler beim Test: {e}")
    
    try:
        # 3. Teste /api/v1/projects/
        print("\n📊 TESTE /api/v1/projects/:")
        response = requests.get(f"{base_url}/api/v1/projects/", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            projects = response.json()
            print(f"   Projekte gefunden: {len(projects)}")
            for i, project in enumerate(projects):
                print(f"   - {i+1}. {project.get('name', 'N/A')} (ID: {project.get('id', 'N/A')})")
        else:
            print(f"   ❌ Fehler: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Fehler beim Test: {e}")

if __name__ == "__main__":
    check_backend_milestones() 