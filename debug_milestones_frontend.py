#!/usr/bin/env python3
"""
Debug-Skript für Milestones-API
Testet die API direkt, um zu sehen, ob das Backend korrekt funktioniert
"""

import requests
import json
from datetime import datetime

# API-Konfiguration
BASE_URL = "http://localhost:8000/api/v1"
LOGIN_URL = f"{BASE_URL}/auth/login"
MILESTONES_URL = f"{BASE_URL}/milestones"
ALL_MILESTONES_URL = f"{BASE_URL}/milestones/all"
PROJECTS_URL = f"{BASE_URL}/projects"

def login():
    """Login als admin und Token holen"""
    print("🔐 Logging in as admin...")
    
    login_data = {
        "username": "admin@buildwise.de",
        "password": "admin123"
    }
    
    response = requests.post(LOGIN_URL, data=login_data)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        user = data.get("user")
        print(f"✅ Login successful")
        print(f"👤 User: {user.get('first_name')} {user.get('last_name')} ({user.get('user_type')})")
        return token
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def get_projects(token):
    """Projekte abrufen"""
    print("\n📋 Getting projects...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(PROJECTS_URL, headers=headers)
    
    if response.status_code == 200:
        projects = response.json()
        print(f"✅ Found {len(projects)} projects:")
        for project in projects:
            print(f"  - Project {project['id']}: {project['name']} ({project['status']})")
        return projects
    else:
        print(f"❌ Failed to get projects: {response.status_code}")
        print(f"Response: {response.text}")
        return []

def get_milestones_for_project(token, project_id):
    """Milestones für ein spezifisches Projekt abrufen"""
    print(f"\n🏗️ Getting milestones for project {project_id}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    params = {"project_id": project_id}
    response = requests.get(MILESTONES_URL, headers=headers, params=params)
    
    if response.status_code == 200:
        milestones = response.json()
        print(f"✅ Found {len(milestones)} milestones for project {project_id}:")
        for milestone in milestones:
            print(f"  - Milestone {milestone['id']}: {milestone['title']} ({milestone['status']})")
        return milestones
    else:
        print(f"❌ Failed to get milestones for project {project_id}: {response.status_code}")
        print(f"Response: {response.text}")
        return []

def get_all_milestones(token):
    """Alle Milestones abrufen (für Dienstleister)"""
    print(f"\n👷 Getting all milestones (service provider view)...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(ALL_MILESTONES_URL, headers=headers)
    
    if response.status_code == 200:
        milestones = response.json()
        print(f"✅ Found {len(milestones)} milestones (all):")
        for milestone in milestones:
            print(f"  - Milestone {milestone['id']}: {milestone['title']} ({milestone['status']}) - Project: {milestone.get('project_id', 'N/A')}")
        return milestones
    else:
        print(f"❌ Failed to get all milestones: {response.status_code}")
        print(f"Response: {response.text}")
        return []

def main():
    print("🚀 Starting Milestones API Debug...")
    print("=" * 50)
    
    # Login
    token = login()
    if not token:
        print("❌ Cannot proceed without valid token")
        return
    
    # Projekte abrufen
    projects = get_projects(token)
    if not projects:
        print("❌ No projects found, cannot test milestones")
        return
    
    # Teste Milestones für das erste Projekt
    first_project = projects[0]
    project_milestones = get_milestones_for_project(token, first_project['id'])
    
    # Teste alle Milestones (Dienstleister-Ansicht)
    all_milestones = get_all_milestones(token)
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY:")
    print(f"  - Projects found: {len(projects)}")
    print(f"  - Milestones for project {first_project['id']}: {len(project_milestones)}")
    print(f"  - All milestones (service provider): {len(all_milestones)}")
    
    if project_milestones and all_milestones:
        print("✅ Both API endpoints working correctly")
    elif project_milestones and not all_milestones:
        print("⚠️ Project milestones work, but all milestones endpoint has issues")
    elif not project_milestones and all_milestones:
        print("⚠️ All milestones work, but project milestones endpoint has issues")
    else:
        print("❌ Both endpoints have issues")

if __name__ == "__main__":
    main() 