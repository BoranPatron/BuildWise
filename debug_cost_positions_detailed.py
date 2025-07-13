#!/usr/bin/env python3
"""
Detailliertes Debug-Skript für Kostenpositionen
Überprüft Backend-Logs und Datenbank-Zustand
"""

import requests
import json
import sqlite3
from datetime import datetime

def check_database_state():
    """Überprüft den Zustand der Datenbank"""
    
    print("🔍 Überprüfe Datenbank-Zustand...")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('buildwise.db')
        cursor = conn.cursor()
        
        # Prüfe cost_positions Tabelle
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cost_positions'")
        if cursor.fetchone():
            print("✅ cost_positions Tabelle existiert")
            
            # Zeige alle Einträge
            cursor.execute("SELECT id, title, category, cost_type, status, project_id FROM cost_positions")
            rows = cursor.fetchall()
            print(f"📊 Anzahl Einträge: {len(rows)}")
            
            if rows:
                print("\n📋 Alle Kostenpositionen:")
                for row in rows:
                    print(f"   - ID: {row[0]}, Titel: {row[1]}, Kategorie: {row[2]}, Cost Type: {row[3]}, Status: {row[4]}, Projekt: {row[5]}")
            else:
                print("⚠️ Keine Kostenpositionen in der Datenbank")
        else:
            print("❌ cost_positions Tabelle existiert nicht")
        
        # Prüfe quotes Tabelle
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quotes'")
        if cursor.fetchone():
            print("\n✅ quotes Tabelle existiert")
            
            cursor.execute("SELECT id, title, status, project_id FROM quotes WHERE project_id = 4")
            rows = cursor.fetchall()
            print(f"📊 Angebote für Projekt 4: {len(rows)}")
            
            if rows:
                print("\n📋 Angebote für Projekt 4:")
                for row in rows:
                    print(f"   - ID: {row[0]}, Titel: {row[1]}, Status: {row[2]}, Projekt: {row[3]}")
        else:
            print("❌ quotes Tabelle existiert nicht")
        
        # Prüfe projects Tabelle
        cursor.execute("SELECT id, name, status FROM projects WHERE id = 4")
        row = cursor.fetchone()
        if row:
            print(f"\n✅ Projekt 4 gefunden: {row[1]} (Status: {row[2]})")
        else:
            print("\n❌ Projekt 4 nicht gefunden")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Datenbank-Fehler: {e}")

def test_api_with_debug():
    """Testet die API mit detailliertem Debug"""
    
    print("\n🔍 Teste API mit Debug...")
    print("=" * 50)
    
    # 1. Login
    print("\n1️⃣ Login...")
    login_data = {
        'username': 'admin@buildwise.de',
        'password': 'admin123'
    }
    
    try:
        response = requests.post(
            'http://localhost:8000/api/v1/auth/login',
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        print(f"📡 Login Status: {response.status_code}")
        print(f"📡 Login Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            token = data['access_token']
            print("✅ Login erfolgreich")
            print(f"👤 User: {data['user']['first_name']} {data['user']['last_name']}")
            print(f"🔑 Token: {token[:20]}...")
        else:
            print(f"❌ Login fehlgeschlagen")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Login-Fehler: {e}")
        return False
    
    # 2. Teste verschiedene API-Endpunkte
    headers = {'Authorization': f'Bearer {token}'}
    
    # Teste Projekte
    print("\n2️⃣ Teste Projekte API...")
    try:
        response = requests.get('http://localhost:8000/api/v1/projects/', headers=headers)
        print(f"📡 Projekte Status: {response.status_code}")
        if response.status_code == 200:
            projects = response.json()
            print(f"✅ Projekte geladen: {len(projects)} Projekte")
        else:
            print(f"❌ Projekte-Fehler: {response.text}")
    except Exception as e:
        print(f"❌ Projekte-Exception: {e}")
    
    # Teste Angebote
    print("\n3️⃣ Teste Angebote API...")
    try:
        response = requests.get('http://localhost:8000/api/v1/quotes/?project_id=4', headers=headers)
        print(f"📡 Angebote Status: {response.status_code}")
        if response.status_code == 200:
            quotes = response.json()
            print(f"✅ Angebote geladen: {len(quotes)} Angebote")
        else:
            print(f"❌ Angebote-Fehler: {response.text}")
    except Exception as e:
        print(f"❌ Angebote-Exception: {e}")
    
    # Teste Kostenpositionen ohne Filter
    print("\n4️⃣ Teste Kostenpositionen ohne Filter...")
    try:
        response = requests.get('http://localhost:8000/api/v1/cost-positions/', headers=headers)
        print(f"📡 Kostenpositionen Status: {response.status_code}")
        if response.status_code == 200:
            cost_positions = response.json()
            print(f"✅ Kostenpositionen geladen: {len(cost_positions)} Einträge")
        else:
            print(f"❌ Kostenpositionen-Fehler: {response.text}")
    except Exception as e:
        print(f"❌ Kostenpositionen-Exception: {e}")
    
    # Teste Kostenpositionen mit Projekt-Filter
    print("\n5️⃣ Teste Kostenpositionen mit Projekt-Filter...")
    try:
        response = requests.get('http://localhost:8000/api/v1/cost-positions/?project_id=4', headers=headers)
        print(f"📡 Kostenpositionen (Projekt 4) Status: {response.status_code}")
        if response.status_code == 200:
            cost_positions = response.json()
            print(f"✅ Kostenpositionen (Projekt 4) geladen: {len(cost_positions)} Einträge")
        else:
            print(f"❌ Kostenpositionen (Projekt 4)-Fehler: {response.text}")
    except Exception as e:
        print(f"❌ Kostenpositionen (Projekt 4)-Exception: {e}")
    
    # Teste Kostenpositionen mit accepted_quotes_only
    print("\n6️⃣ Teste Kostenpositionen mit accepted_quotes_only...")
    try:
        response = requests.get('http://localhost:8000/api/v1/cost-positions/?accepted_quotes_only=true', headers=headers)
        print(f"📡 Kostenpositionen (accepted_quotes_only) Status: {response.status_code}")
        if response.status_code == 200:
            cost_positions = response.json()
            print(f"✅ Kostenpositionen (accepted_quotes_only) geladen: {len(cost_positions)} Einträge")
        else:
            print(f"❌ Kostenpositionen (accepted_quotes_only)-Fehler: {response.text}")
    except Exception as e:
        print(f"❌ Kostenpositionen (accepted_quotes_only)-Exception: {e}")
    
    # Teste kombinierte Filter
    print("\n7️⃣ Teste kombinierte Filter...")
    try:
        response = requests.get('http://localhost:8000/api/v1/cost-positions/?project_id=4&accepted_quotes_only=true', headers=headers)
        print(f"📡 Kombinierte Filter Status: {response.status_code}")
        if response.status_code == 200:
            cost_positions = response.json()
            print(f"✅ Kombinierte Filter geladen: {len(cost_positions)} Einträge")
        else:
            print(f"❌ Kombinierte Filter-Fehler: {response.text}")
    except Exception as e:
        print(f"❌ Kombinierte Filter-Exception: {e}")

if __name__ == "__main__":
    check_database_state()
    test_api_with_debug() 