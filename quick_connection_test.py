#!/usr/bin/env python3
"""
Schneller Verbindungstest für Backend und Datenbank
"""

import requests
import sqlite3
import time
import os

def test_backend_connection():
    """Testet die Backend-Verbindung und Datenbank"""
    print("🔍 Teste Backend-Verbindung...")
    
    # Backend-URL
    base_url = "http://localhost:8000"
    
    # Admin-Token
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBidWlsZHdpc2UuZGUiLCJleHAiOjE3NTI5NDY2OTh9.QybsYBe-4RUGdICzDAplsIzxmuaDGHTLMp5_k3YfKNA",
        "Content-Type": "application/json"
    }
    
    # 1. Backend-Verfügbarkeit testen
    print("\n1️⃣ Backend-Verfügbarkeit:")
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        print(f"   ✅ Backend erreichbar: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Backend nicht erreichbar: {e}")
        print("   💡 Starte Backend neu...")
        return False
    
    # 2. Authentifizierung testen
    print("\n2️⃣ Authentifizierung:")
    try:
        response = requests.get(f"{base_url}/api/v1/users/me", headers=headers)
        print(f"   🔐 Auth-Status: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"   ✅ User: {user_data.get('email', 'N/A')} (ID: {user_data.get('id', 'N/A')})")
        else:
            print(f"   ❌ Auth-Fehler: {response.text}")
    except Exception as e:
        print(f"   ❌ Auth-Test fehlgeschlagen: {e}")
    
    # 3. Datenbank testen
    print("\n3️⃣ Datenbank-Status:")
    if os.path.exists('buildwise.db'):
        print(f"   ✅ buildwise.db gefunden: {os.path.getsize('buildwise.db')} Bytes")
        
        conn = sqlite3.connect('buildwise.db')
        cursor = conn.cursor()
        
        try:
            # Tabellen prüfen
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"   📋 Tabellen: {len(tables)}")
            
            # Audit Logs prüfen
            cursor.execute("SELECT COUNT(*) FROM audit_logs")
            audit_count = cursor.fetchone()[0]
            print(f"   📊 Audit Logs: {audit_count}")
            
            # Milestones prüfen
            cursor.execute("SELECT COUNT(*) FROM milestones")
            milestones_count = cursor.fetchone()[0]
            print(f"   🏗️ Milestones: {milestones_count}")
            
            # Letzte Audit Logs
            cursor.execute("SELECT id, action, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 3")
            recent_logs = cursor.fetchall()
            print(f"   📋 Letzte Audit Logs:")
            for log in recent_logs:
                print(f"   - ID {log[0]}: {log[1]} ({log[2]})")
                
        except Exception as e:
            print(f"   ❌ Datenbank-Fehler: {e}")
        finally:
            conn.close()
    else:
        print("   ❌ buildwise.db nicht gefunden")
    
    # 4. API-Endpoints testen
    print("\n4️⃣ API-Endpoints:")
    
    # Milestones API
    try:
        response = requests.get(f"{base_url}/api/v1/milestones/all", headers=headers)
        print(f"   📋 /milestones/all: {response.status_code}")
        if response.status_code == 200:
            milestones = response.json()
            print(f"   - Milestones gefunden: {len(milestones)}")
    except Exception as e:
        print(f"   ❌ Milestones API: {e}")
    
    # Quotes API
    try:
        response = requests.get(f"{base_url}/api/v1/quotes/", headers=headers)
        print(f"   💰 /quotes/: {response.status_code}")
        if response.status_code == 200:
            quotes = response.json()
            print(f"   - Quotes gefunden: {len(quotes)}")
    except Exception as e:
        print(f"   ❌ Quotes API: {e}")
    
    print("\n✅ Verbindungstest abgeschlossen!")
    return True

if __name__ == "__main__":
    test_backend_connection() 