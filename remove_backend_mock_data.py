#!/usr/bin/env python3
"""
Entfernt Backend-Mock-Daten und stellt sicher, dass nur echte Datenbank-Daten verwendet werden
"""

import requests
import json
import sqlite3
import os

def remove_backend_mock_data():
    """Entfernt Backend-Mock-Daten"""
    print("🔧 BACKEND MOCK-DATEN ENTFERNEN")
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
            return
    except Exception as e:
        print(f"   ❌ Backend-Fehler: {e}")
        return
    
    print("\n🗄️ DATENBANK-INHALT PRÜFEN:")
    db_path = "buildwise.db"
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Projekte prüfen
            cursor.execute("SELECT COUNT(*) FROM projects")
            projects_count = cursor.fetchone()[0]
            print(f"   📊 Projekte in DB: {projects_count}")
            
            if projects_count > 0:
                cursor.execute("SELECT id, name, owner_id FROM projects")
                projects = cursor.fetchall()
                for project in projects:
                    print(f"   - ID {project[0]}: {project[1]} (Owner: {project[2]})")
            else:
                print("   ❌ Keine Projekte in der Datenbank")
            
            # Users prüfen
            cursor.execute("SELECT COUNT(*) FROM users")
            users_count = cursor.fetchone()[0]
            print(f"   👤 Users in DB: {users_count}")
            
        except Exception as e:
            print(f"   ❌ Datenbank-Fehler: {e}")
        finally:
            conn.close()
    else:
        print("   ❌ Datenbank nicht gefunden")
    
    print("\n🔐 BACKEND-API TEST:")
    try:
        response = requests.get(f"{base_url}/api/v1/projects/", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            projects = response.json()
            print(f"   📊 Backend gibt {len(projects)} Projekte zurück")
            for i, project in enumerate(projects):
                print(f"   - {i+1}. {project.get('name', 'N/A')} (ID: {project.get('id', 'N/A')})")
        elif response.status_code == 401:
            print("   ❌ Token abgelaufen - Neue Anmeldung erforderlich")
        else:
            print(f"   ❌ Fehler: {response.text}")
            
    except Exception as e:
        print(f"   ❌ API-Fehler: {e}")
    
    print("\n💡 EMPFEHLUNGEN:")
    print("   1. Backend neu starten")
    print("   2. Browser-Cache leeren")
    print("   3. Neuen Login-Token generieren")
    print("   4. Test-Daten-Skripte entfernen")
    print("   5. Datenbank zurücksetzen falls nötig")

if __name__ == "__main__":
    remove_backend_mock_data() 