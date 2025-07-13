#!/usr/bin/env python3
"""
Finales Test-Skript für Kostenpositionen
Testet die API nach den Enum-Korrekturen
"""

import requests
import json
from datetime import datetime

def test_cost_positions_api():
    """Testet die Kostenpositionen-API"""
    
    print("🔍 Finaler Test: Kostenpositionen API")
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
            print(f"👤 User: {data['user']['first_name']} {data['user']['last_name']}")
        else:
            print(f"❌ Login fehlgeschlagen: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Login-Fehler: {e}")
        return False
    
    # 2. Teste Kostenpositionen für Projekt 4
    print("\n2️⃣ Teste Kostenpositionen für Projekt 4...")
    
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(
            'http://localhost:8000/api/v1/cost-positions/?project_id=4&accepted_quotes_only=true',
            headers=headers
        )
        
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            cost_positions = response.json()
            print(f"✅ Kostenpositionen erfolgreich geladen: {len(cost_positions)} Einträge")
            
            if cost_positions:
                print("\n📊 Erste Kostenposition:")
                first_cp = cost_positions[0]
                print(f"   - ID: {first_cp['id']}")
                print(f"   - Titel: {first_cp['title']}")
                print(f"   - Kategorie: {first_cp['category']}")
                print(f"   - Cost Type: {first_cp['cost_type']}")
                print(f"   - Status: {first_cp['status']}")
                print(f"   - Betrag: {first_cp['amount']} {first_cp['currency']}")
            else:
                print("⚠️ Keine Kostenpositionen gefunden")
                
        else:
            print(f"❌ Fehler beim Laden der Kostenpositionen: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API-Fehler: {e}")
        return False
    
    # 3. Teste Projekte
    print("\n3️⃣ Teste Projekte...")
    
    try:
        response = requests.get(
            'http://localhost:8000/api/v1/projects/',
            headers=headers
        )
        
        if response.status_code == 200:
            projects = response.json()
            print(f"✅ Projekte erfolgreich geladen: {len(projects)} Projekte")
            
            # Zeige Projekt 4
            project_4 = next((p for p in projects if p['id'] == 4), None)
            if project_4:
                print(f"📋 Projekt 4: {project_4['name']}")
                print(f"   - Status: {project_4['status']}")
                print(f"   - Budget: {project_4.get('budget', 'Nicht gesetzt')}")
            else:
                print("⚠️ Projekt 4 nicht gefunden")
        else:
            print(f"❌ Fehler beim Laden der Projekte: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Projekte-Fehler: {e}")
    
    # 4. Teste Angebote für Projekt 4
    print("\n4️⃣ Teste Angebote für Projekt 4...")
    
    try:
        response = requests.get(
            'http://localhost:8000/api/v1/quotes/?project_id=4',
            headers=headers
        )
        
        if response.status_code == 200:
            quotes = response.json()
            print(f"✅ Angebote erfolgreich geladen: {len(quotes)} Angebote")
            
            accepted_quotes = [q for q in quotes if q['status'] == 'accepted']
            print(f"📊 Akzeptierte Angebote: {len(accepted_quotes)}")
            
            if accepted_quotes:
                print("📋 Akzeptierte Angebote:")
                for quote in accepted_quotes:
                    print(f"   - ID: {quote['id']}, Titel: {quote['title']}, Betrag: {quote['total_amount']}")
            else:
                print("⚠️ Keine akzeptierten Angebote gefunden")
        else:
            print(f"❌ Fehler beim Laden der Angebote: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Angebote-Fehler: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Finaler Test abgeschlossen!")
    return True

if __name__ == "__main__":
    test_cost_positions_api() 