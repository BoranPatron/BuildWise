#!/usr/bin/env python3
"""
Überprüft die Projekt-Ladung im Backend
"""

import requests
import json

def debug_project_loading():
    """Überprüft die Projekt-Ladung im Backend"""
    print("🔍 PROJEKT-LADUNG DEBUG")
    print("=" * 40)
    
    base_url = "http://localhost:8000"
    
    # Admin-Token (möglicherweise abgelaufen)
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBidWlsZHdpc2UuZGUiLCJleHAiOjE3NTI5NDY2OTh9.QybsYBe-4RUGdICzDAplsIzxmuaDGHTLMp5_k3YfKNA",
        "Content-Type": "application/json"
    }
    
    print("\n📊 BACKEND-VERFÜGBARKEIT:")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Backend erreichbar")
        else:
            print("   ❌ Backend nicht erreichbar")
    except Exception as e:
        print(f"   ❌ Backend-Fehler: {e}")
        return
    
    print("\n🔐 TOKEN-VALIDIERUNG:")
    try:
        response = requests.get(f"{base_url}/api/v1/projects/", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            projects = response.json()
            print(f"   ✅ Token gültig - {len(projects)} Projekte gefunden")
            for i, project in enumerate(projects):
                print(f"   - {i+1}. {project.get('name', 'N/A')} (ID: {project.get('id', 'N/A')})")
        elif response.status_code == 401:
            print("   ❌ Token abgelaufen - Neue Anmeldung erforderlich")
        else:
            print(f"   ❌ Fehler: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
    
    print("\n🎭 MOCK-DATEN PRÜFUNG:")
    print("   📋 Suche nach Mock-Daten im Backend-Code...")
    
    # Prüfe Backend-Code auf Mock-Daten
    backend_files = [
        "app/services/project_service.py",
        "app/api/projects.py",
        "app/main.py"
    ]
    
    for file_path in backend_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'mock' in content.lower() or 'test' in content.lower():
                    print(f"   ⚠️  Mögliche Mock-Daten in: {file_path}")
        except FileNotFoundError:
            print(f"   ❌ Datei nicht gefunden: {file_path}")
    
    print("\n💡 EMPFEHLUNGEN:")
    print("   1. Browser-Cache leeren")
    print("   2. Neuen Login-Token generieren")
    print("   3. Backend-Mock-Daten entfernen")
    print("   4. Frontend-Backend-Synchronisation testen")

if __name__ == "__main__":
    debug_project_loading() 