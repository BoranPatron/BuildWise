#!/usr/bin/env python3
"""
Debug-Skript zur Analyse des Gewerk-Erstellungs-Datenflusses
"""

import requests
import json
import sqlite3
import os
from datetime import datetime

def debug_milestone_creation_flow():
    """Analysiert den kompletten Datenfluss bei der Gewerk-Erstellung"""
    print("🔍 Analysiere Gewerk-Erstellungs-Datenfluss...")
    
    # Backend-URL
    base_url = "http://localhost:8000"
    
    # Admin-Token
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBidWlsZHdpc2UuZGUiLCJleHAiOjE3NTI5NDY2OTh9.QybsYBe-4RUGdICzDAplsIzxmuaDGHTLMp5_k3YfKNA",
        "Content-Type": "application/json"
    }
    
    print("\n📊 DATENFLUSS-ANALYSE:")
    print("=" * 40)
    
    # 1. Aktueller Datenbank-Status
    print("\n1️⃣ Aktueller Datenbank-Status:")
    if os.path.exists('buildwise.db'):
        conn = sqlite3.connect('buildwise.db')
        cursor = conn.cursor()
        
        try:
            # Projekte
            cursor.execute("SELECT COUNT(*) FROM projects")
            projects_count = cursor.fetchone()[0]
            print(f"   📋 Projekte in DB: {projects_count}")
            
            if projects_count > 0:
                cursor.execute("SELECT id, name, owner_id FROM projects LIMIT 3")
                for row in cursor.fetchall():
                    print(f"   - ID {row[0]}: {row[1]} (Owner: {row[2]})")
            
            # Milestones
            cursor.execute("SELECT COUNT(*) FROM milestones")
            milestones_count = cursor.fetchone()[0]
            print(f"   🏗️ Milestones in DB: {milestones_count}")
            
            if milestones_count > 0:
                cursor.execute("SELECT id, title, project_id, status FROM milestones LIMIT 3")
                for row in cursor.fetchall():
                    print(f"   - ID {row[0]}: {row[1]} (Projekt: {row[2]}, Status: {row[3]})")
            
            # Users
            cursor.execute("SELECT COUNT(*) FROM users")
            users_count = cursor.fetchone()[0]
            print(f"   👤 Users in DB: {users_count}")
            
        except Exception as e:
            print(f"   ❌ Datenbank-Fehler: {e}")
        finally:
            conn.close()
    else:
        print("   ❌ buildwise.db nicht gefunden")
    
    # 2. Teste Gewerk-Erstellung
    print("\n2️⃣ Teste Gewerk-Erstellung:")
    try:
        # Erstelle ein Test-Gewerk
        test_milestone_data = {
            "title": "Test Gewerk Debug",
            "description": "Test-Gewerk für Debug-Zwecke",
            "project_id": 1,  # Verwende erstes Projekt
            "status": "planned",
            "priority": "medium",
            "category": "test",
            "planned_date": "2024-12-31",
            "is_critical": False,
            "notify_on_completion": True,
            "notes": "Debug-Test"
        }
        
        print(f"   📡 Sende Test-Gewerk-Daten: {test_milestone_data}")
        response = requests.post(f"{base_url}/api/v1/milestones/", 
                               headers=headers, 
                               json=test_milestone_data)
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            created_milestone = response.json()
            print(f"   ✅ Gewerk erfolgreich erstellt: ID {created_milestone.get('id')}")
            print(f"   📋 Details: {created_milestone}")
        else:
            print(f"   ❌ Fehler: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Fehler beim Test: {e}")
    
    # 3. Überprüfe Datenbank nach Erstellung
    print("\n3️⃣ Überprüfe Datenbank nach Erstellung:")
    if os.path.exists('buildwise.db'):
        conn = sqlite3.connect('buildwise.db')
        cursor = conn.cursor()
        
        try:
            # Milestones nach Erstellung
            cursor.execute("SELECT COUNT(*) FROM milestones")
            new_milestones_count = cursor.fetchone()[0]
            print(f"   🏗️ Milestones nach Erstellung: {new_milestones_count}")
            
            if new_milestones_count > 0:
                cursor.execute("SELECT id, title, project_id, status, created_at FROM milestones ORDER BY id DESC LIMIT 3")
                for row in cursor.fetchall():
                    print(f"   - ID {row[0]}: {row[1]} (Projekt: {row[2]}, Status: {row[3]}, Erstellt: {row[4]})")
            
        except Exception as e:
            print(f"   ❌ Datenbank-Fehler: {e}")
        finally:
            conn.close()
    
    # 4. Teste Gewerk-Abruf
    print("\n4️⃣ Teste Gewerk-Abruf:")
    try:
        # Teste /milestones/all
        response = requests.get(f"{base_url}/api/v1/milestones/all", headers=headers)
        print(f"   📡 /milestones/all Status: {response.status_code}")
        if response.status_code == 200:
            milestones = response.json()
            print(f"   📋 Gefundene Milestones: {len(milestones)}")
            for i, milestone in enumerate(milestones[:3]):
                print(f"   - {i+1}. {milestone.get('title', 'N/A')} (ID: {milestone.get('id', 'N/A')})")
        else:
            print(f"   ❌ Fehler: {response.text}")
            
        # Teste /milestones?project_id=1
        response = requests.get(f"{base_url}/api/v1/milestones?project_id=1", headers=headers)
        print(f"   📡 /milestones?project_id=1 Status: {response.status_code}")
        if response.status_code == 200:
            milestones = response.json()
            print(f"   📋 Projekt-Milestones: {len(milestones)}")
            for i, milestone in enumerate(milestones[:3]):
                print(f"   - {i+1}. {milestone.get('title', 'N/A')} (ID: {milestone.get('id', 'N/A')})")
        else:
            print(f"   ❌ Fehler: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Fehler beim Test: {e}")
    
    print("\n💡 DATENFLUSS-ANALYSE:")
    print("=" * 30)
    
    print("Frontend → Backend Datenfluss:")
    print("1. Frontend: handleCreateTradeWithForm()")
    print("2. Frontend: createMilestone(milestoneData)")
    print("3. Frontend: api.post('/milestones', data)")
    print("4. Backend: POST /api/v1/milestones/")
    print("5. Backend: create_new_milestone()")
    print("6. Backend: create_milestone() Service")
    print("7. Backend: db.add(milestone) + db.commit()")
    print("8. Datenbank: INSERT INTO milestones")
    
    print("\nMögliche Probleme:")
    print("- Authentifizierung fehlschlägt (401)")
    print("- Projekt-ID existiert nicht")
    print("- Datenbank-Constraints verletzt")
    print("- Backend-Service-Fehler")
    print("- Frontend-Cache zeigt alte Daten")

if __name__ == "__main__":
    debug_milestone_creation_flow() 