#!/usr/bin/env python3
"""
Umfassendes Debug-Skript zur Analyse des kompletten Datenflusses
Frontend → API → Service → Datenbank
"""

import requests
import json
import sqlite3
import os
from datetime import datetime

def debug_complete_data_flow():
    """Analysiert den kompletten Datenfluss von Frontend bis zur Datenbank"""
    print("🔍 Analysiere kompletten Datenfluss...")
    
    # Backend-URL
    base_url = "http://localhost:8000"
    
    # Admin-Token
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBidWlsZHdpc2UuZGUiLCJleHAiOjE3NTI5NDY2OTh9.QybsYBe-4RUGdICzDAplsIzxmuaDGHTLMp5_k3YfKNA",
        "Content-Type": "application/json"
    }
    
    print("\n📊 DATENFLUSS-ANALYSE:")
    print("=" * 50)
    
    # 1. Datenbank-Konfiguration prüfen
    print("\n1️⃣ DATENBANK-KONFIGURATION:")
    print("-" * 30)
    
    if os.path.exists('buildwise.db'):
        print(f"   ✅ buildwise.db gefunden: {os.path.getsize('buildwise.db')} Bytes")
        
        # Datenbank-Details
        conn = sqlite3.connect('buildwise.db')
        cursor = conn.cursor()
        
        try:
            # Tabellen auflisten
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"   📋 Tabellen in DB: {len(tables)}")
            for table in tables:
                print(f"   - {table[0]}")
            
            # Milestones-Tabelle Details
            cursor.execute("PRAGMA table_info(milestones);")
            columns = cursor.fetchall()
            print(f"   🏗️ Milestones-Schema: {len(columns)} Spalten")
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")
            
        except Exception as e:
            print(f"   ❌ Datenbank-Fehler: {e}")
        finally:
            conn.close()
    else:
        print("   ❌ buildwise.db nicht gefunden")
    
    # 2. Aktuelle Datenbank-Inhalte
    print("\n2️⃣ AKTUELLE DATENBANK-INHALTE:")
    print("-" * 35)
    
    if os.path.exists('buildwise.db'):
        conn = sqlite3.connect('buildwise.db')
        cursor = conn.cursor()
        
        try:
            # Projekte
            cursor.execute("SELECT COUNT(*) FROM projects")
            projects_count = cursor.fetchone()[0]
            print(f"   📋 Projekte: {projects_count}")
            
            if projects_count > 0:
                cursor.execute("SELECT id, name, owner_id FROM projects LIMIT 3")
                for row in cursor.fetchall():
                    print(f"   - ID {row[0]}: {row[1]} (Owner: {row[2]})")
            
            # Milestones
            cursor.execute("SELECT COUNT(*) FROM milestones")
            milestones_count = cursor.fetchone()[0]
            print(f"   🏗️ Milestones: {milestones_count}")
            
            if milestones_count > 0:
                cursor.execute("SELECT id, title, project_id, status, created_at FROM milestones ORDER BY id DESC LIMIT 3")
                for row in cursor.fetchall():
                    print(f"   - ID {row[0]}: {row[1]} (Projekt: {row[2]}, Status: {row[3]}, Erstellt: {row[4]})")
            
            # Users
            cursor.execute("SELECT COUNT(*) FROM users")
            users_count = cursor.fetchone()[0]
            print(f"   👤 Users: {users_count}")
            
            if users_count > 0:
                cursor.execute("SELECT id, email, user_type FROM users LIMIT 3")
                for row in cursor.fetchall():
                    print(f"   - ID {row[0]}: {row[1]} (Typ: {row[2]})")
            
        except Exception as e:
            print(f"   ❌ Datenbank-Fehler: {e}")
        finally:
            conn.close()
    
    # 3. API-Tests
    print("\n3️⃣ API-TESTS:")
    print("-" * 15)
    
    # Teste Backend-Verfügbarkeit
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        print(f"   ✅ Backend erreichbar: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Backend nicht erreichbar: {e}")
        return
    
    # Teste Authentifizierung
    try:
        response = requests.get(f"{base_url}/api/v1/users/me", headers=headers)
        print(f"   🔐 Auth-Test: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"   - User: {user_data.get('email', 'N/A')} (ID: {user_data.get('id', 'N/A')})")
        else:
            print(f"   - Auth-Fehler: {response.text}")
    except Exception as e:
        print(f"   ❌ Auth-Test fehlgeschlagen: {e}")
    
    # 4. Gewerk-Erstellung testen
    print("\n4️⃣ GEWERK-ERSTELLUNG TEST:")
    print("-" * 30)
    
    try:
        # Erstelle Test-Gewerk
        test_milestone_data = {
            "title": "Debug Test Gewerk",
            "description": "Test-Gewerk für Datenfluss-Analyse",
            "project_id": 1,  # Verwende erstes Projekt
            "status": "planned",
            "priority": "medium",
            "category": "debug",
            "planned_date": "2024-12-31",
            "is_critical": False,
            "notify_on_completion": True,
            "notes": "Debug-Test"
        }
        
        print(f"   📡 Sende Test-Daten: {test_milestone_data}")
        response = requests.post(f"{base_url}/api/v1/milestones/", 
                               headers=headers, 
                               json=test_milestone_data)
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            created_milestone = response.json()
            print(f"   ✅ Gewerk erstellt: ID {created_milestone.get('id')}")
            print(f"   📋 Details: {created_milestone}")
            
            # Überprüfe Datenbank nach Erstellung
            conn = sqlite3.connect('buildwise.db')
            cursor = conn.cursor()
            
            try:
                cursor.execute("SELECT COUNT(*) FROM milestones")
                new_count = cursor.fetchone()[0]
                print(f"   🗄️ Milestones in DB nach Erstellung: {new_count}")
                
                if new_count > milestones_count:
                    cursor.execute("SELECT id, title, project_id, status FROM milestones ORDER BY id DESC LIMIT 1")
                    latest = cursor.fetchone()
                    print(f"   🆕 Neuestes Gewerk: ID {latest[0]}: {latest[1]} (Projekt: {latest[2]}, Status: {latest[3]})")
                
            except Exception as e:
                print(f"   ❌ DB-Check-Fehler: {e}")
            finally:
                conn.close()
        else:
            print(f"   ❌ Erstellungs-Fehler: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Test-Fehler: {e}")
    
    # 5. Datenfluss-Analyse
    print("\n5️⃣ DATENFLUSS-ANALYSE:")
    print("-" * 25)
    
    print("Frontend → Backend Datenfluss:")
    print("1. Frontend: handleCreateTradeWithForm()")
    print("2. Frontend: createMilestone(milestoneData)")
    print("3. Frontend: api.post('/milestones', data)")
    print("4. Backend: POST /api/v1/milestones/")
    print("5. Backend: create_new_milestone() Endpoint")
    print("6. Backend: create_milestone() Service")
    print("7. Backend: db.add(milestone) + db.commit()")
    print("8. Datenbank: INSERT INTO milestones")
    print("9. SQLite: buildwise.db Datei")
    
    print("\nKonfiguration:")
    print("- Datenbank: SQLite (buildwise.db)")
    print("- Engine: sqlite+aiosqlite:///./buildwise.db")
    print("- Pool: StaticPool für SQLite")
    print("- Session: AsyncSessionLocal")
    
    print("\nMögliche Probleme:")
    print("- 401: Authentifizierung fehlschlägt")
    print("- 404: Projekt-ID existiert nicht")
    print("- 422: Validierungsfehler")
    print("- 500: Backend-Service-Fehler")
    print("- DB-Lock: SQLite-Lock-Probleme")
    print("- Cache: Frontend zeigt alte Daten")

if __name__ == "__main__":
    debug_complete_data_flow() 