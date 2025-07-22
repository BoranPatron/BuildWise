#!/usr/bin/env python3
"""
Überprüft Datenbank-Schreibvorgänge und Debug-Logs
"""

import requests
import json
import sqlite3
import os
import time

def debug_database_write():
    """Überprüft Datenbank-Schreibvorgänge"""
    print("🔍 DATENBANK-SCHREIBVORGÄNGE DEBUG")
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
    
    print("\n🗄️ DATENBANK-VORHER:")
    db_path = "buildwise.db"
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Projekte prüfen
            cursor.execute("SELECT COUNT(*) FROM projects")
            projects_count = cursor.fetchone()[0]
            print(f"   📊 Projekte in DB: {projects_count}")
            
            # Users prüfen
            cursor.execute("SELECT COUNT(*) FROM users")
            users_count = cursor.fetchone()[0]
            print(f"   👤 Users in DB: {users_count}")
            
            # Milestones prüfen
            cursor.execute("SELECT COUNT(*) FROM milestones")
            milestones_count = cursor.fetchone()[0]
            print(f"   🎯 Milestones in DB: {milestones_count}")
            
            # Quotes prüfen
            cursor.execute("SELECT COUNT(*) FROM quotes")
            quotes_count = cursor.fetchone()[0]
            print(f"   💰 Quotes in DB: {quotes_count}")
            
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
    print("   1. Backend-Logs prüfen für Debug-Ausgaben")
    print("   2. Neues Projekt erstellen und Logs beobachten")
    print("   3. Datenbank nach Projekt-Erstellung prüfen")
    print("   4. Browser-Cache leeren")
    print("   5. Neuen Login-Token generieren")

if __name__ == "__main__":
    debug_database_write() 