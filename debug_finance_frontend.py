#!/usr/bin/env python3
"""
Debug-Skript für Finance-Seite Frontend
Überprüft API-Aufrufe und Datenfluss
"""

import requests
import json
from datetime import datetime

def debug_finance_frontend():
    """Debuggt die Finance-Seite Frontend"""
    
    print("🔍 Debug: Finance-Seite Frontend")
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
        
        if response.status_code == 200:
            data = response.json()
            token = data['access_token']
            print("✅ Login erfolgreich")
        else:
            print(f"❌ Login fehlgeschlagen: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Login-Fehler: {e}")
        return
    
    # 2. Teste verschiedene API-Aufrufe für Projekt 4
    print("\n2️⃣ Teste API-Aufrufe für Projekt 4...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test 1: Alle Kostenpositionen für Projekt 4
    print("\n📊 Test 1: Alle Kostenpositionen für Projekt 4")
    try:
        response = requests.get(
            'http://localhost:8000/api/v1/cost-positions/?project_id=4',
            headers=headers
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Anzahl Kostenpositionen: {len(data)}")
            for cp in data:
                print(f"  - ID: {cp['id']}, Titel: {cp['title']}, Status: {cp['status']}, Quote ID: {cp.get('quote_id')}")
        else:
            print(f"Fehler: {response.text}")
    except Exception as e:
        print(f"❌ Fehler: {e}")
    
    # Test 2: Nur akzeptierte Angebote für Projekt 4
    print("\n📊 Test 2: Nur akzeptierte Angebote für Projekt 4")
    try:
        response = requests.get(
            'http://localhost:8000/api/v1/cost-positions/?project_id=4&accepted_quotes_only=true',
            headers=headers
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Anzahl Kostenpositionen (akzeptierte Angebote): {len(data)}")
            for cp in data:
                print(f"  - ID: {cp['id']}, Titel: {cp['title']}, Status: {cp['status']}, Quote ID: {cp.get('quote_id')}")
        else:
            print(f"Fehler: {response.text}")
    except Exception as e:
        print(f"❌ Fehler: {e}")
    
    # Test 3: Alle Angebote für Projekt 4
    print("\n📊 Test 3: Alle Angebote für Projekt 4")
    try:
        response = requests.get(
            'http://localhost:8000/api/v1/quotes/?project_id=4',
            headers=headers
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Anzahl Angebote: {len(data)}")
            accepted_quotes = [q for q in data if q['status'] == 'accepted']
            print(f"Anzahl akzeptierte Angebote: {len(accepted_quotes)}")
            for quote in accepted_quotes:
                print(f"  - ID: {quote['id']}, Titel: {quote['title']}, Status: {quote['status']}")
        else:
            print(f"Fehler: {response.text}")
    except Exception as e:
        print(f"❌ Fehler: {e}")
    
    # Test 4: Prüfe Datenbank direkt
    print("\n📊 Test 4: Datenbank-Zustand")
    try:
        import sqlite3
        conn = sqlite3.connect('buildwise.db')
        cursor = conn.cursor()
        
        # Prüfe akzeptierte Angebote für Projekt 4
        cursor.execute("""
            SELECT id, title, status, project_id 
            FROM quotes 
            WHERE project_id = 4 AND status = 'accepted'
        """)
        accepted_quotes = cursor.fetchall()
        print(f"Akzeptierte Angebote in DB: {len(accepted_quotes)}")
        for quote in accepted_quotes:
            print(f"  - ID: {quote[0]}, Titel: {quote[1]}, Status: {quote[2]}")
        
        # Prüfe Kostenpositionen für Projekt 4
        cursor.execute("""
            SELECT id, title, status, quote_id, project_id 
            FROM cost_positions 
            WHERE project_id = 4
        """)
        cost_positions = cursor.fetchall()
        print(f"Kostenpositionen in DB: {len(cost_positions)}")
        for cp in cost_positions:
            print(f"  - ID: {cp[0]}, Titel: {cp[1]}, Status: {cp[2]}, Quote ID: {cp[3]}")
        
        conn.close()
    except Exception as e:
        print(f"❌ Datenbank-Fehler: {e}")

if __name__ == "__main__":
    debug_finance_frontend() 