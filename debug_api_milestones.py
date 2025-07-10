#!/usr/bin/env python3
"""
Debug-Skript für API-Milestones
"""

import requests
import json
import time

# API-Konfiguration
BASE_URL = "http://localhost:8000/api/v1"
LOGIN_URL = f"{BASE_URL}/auth/login"
MILESTONES_URL = f"{BASE_URL}/milestones/all"

def debug_api_milestones():
    """Debuggt die API-Milestone-Abfrage"""
    
    print("🔍 Debug API-Milestones")
    print("=" * 50)
    
    # Login-Daten für Dienstleister
    login_data = {
        "username": "test-dienstleister@buildwise.de",
        "password": "test1234"
    }
    
    try:
        # 1. Login als Dienstleister
        print("🔐 Login als Dienstleister...")
        login_response = requests.post(LOGIN_URL, data=login_data)
        
        if login_response.status_code != 200:
            print(f"❌ Login fehlgeschlagen: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return False
        
        login_result = login_response.json()
        token = login_result.get("access_token")
        user = login_result.get("user")
        
        print(f"✅ Login erfolgreich!")
        print(f"  Benutzer: {user.get('first_name')} {user.get('last_name')}")
        print(f"  Typ: {user.get('user_type')}")
        print(f"  E-Mail: {user.get('email')}")
        
        # 2. Milestones abrufen mit Debug-Headers
        print("\n📋 Rufe Milestones ab...")
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        print(f"  URL: {MILESTONES_URL}")
        print(f"  Headers: {headers}")
        
        milestones_response = requests.get(MILESTONES_URL, headers=headers)
        
        print(f"  Response Status: {milestones_response.status_code}")
        print(f"  Response Headers: {dict(milestones_response.headers)}")
        
        if milestones_response.status_code != 200:
            print(f"❌ Milestones-Abruf fehlgeschlagen: {milestones_response.status_code}")
            print(f"Response: {milestones_response.text}")
            return False
        
        try:
            milestones = milestones_response.json()
            print(f"✅ Milestones erfolgreich abgerufen!")
            print(f"  Anzahl Milestones: {len(milestones)}")
            print(f"  Response Type: {type(milestones)}")
            print(f"  Response: {json.dumps(milestones, indent=2, default=str)}")
            
            if len(milestones) > 0:
                print("\n📋 Gefundene Milestones:")
                for i, milestone in enumerate(milestones, 1):
                    print(f"  {i}. ID: {milestone.get('id')}")
                    print(f"     Titel: {milestone.get('title')}")
                    print(f"     Status: {milestone.get('status')}")
                    print(f"     Projekt-ID: {milestone.get('project_id')}")
                    print(f"     Kategorie: {milestone.get('category')}")
                    print(f"     Priorität: {milestone.get('priority')}")
                    print(f"     Geplantes Datum: {milestone.get('planned_date')}")
                    print()
            else:
                print("⚠️  Keine Milestones gefunden")
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON-Parsing-Fehler: {e}")
            print(f"Raw Response: {milestones_response.text}")
            return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Verbindung zum Backend fehlgeschlagen")
        print("💡 Stellen Sie sicher, dass das Backend läuft: python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Fehler beim Testen: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_bautraeger_comparison():
    """Testet Bauträger zum Vergleich"""
    
    print("\n🔍 Vergleich: Bauträger-Milestones")
    print("=" * 50)
    
    # Login-Daten für Bauträger
    login_data = {
        "username": "admin@buildwise.de",
        "password": "admin123"
    }
    
    try:
        # 1. Login als Bauträger
        print("🔐 Login als Bauträger...")
        login_response = requests.post(LOGIN_URL, data=login_data)
        
        if login_response.status_code != 200:
            print(f"❌ Login fehlgeschlagen: {login_response.status_code}")
            return False
        
        login_result = login_response.json()
        token = login_result.get("access_token")
        user = login_result.get("user")
        
        print(f"✅ Login erfolgreich!")
        print(f"  Benutzer: {user.get('first_name')} {user.get('last_name')}")
        print(f"  Typ: {user.get('user_type')}")
        
        # 2. Milestones abrufen
        print("\n📋 Rufe Milestones ab...")
        headers = {"Authorization": f"Bearer {token}"}
        milestones_response = requests.get(MILESTONES_URL, headers=headers)
        
        if milestones_response.status_code != 200:
            print(f"❌ Milestones-Abruf fehlgeschlagen: {milestones_response.status_code}")
            return False
        
        milestones = milestones_response.json()
        print(f"✅ Milestones erfolgreich abgerufen!")
        print(f"  Anzahl Milestones: {len(milestones)}")
        print(f"  Response: {json.dumps(milestones, indent=2, default=str)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Bauträger-Test: {e}")
        return False

def main():
    """Hauptfunktion"""
    print("🧪 API-Milestones Debug")
    print("=" * 60)
    print(f"⏰ Zeitstempel: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Warte kurz, damit das Backend starten kann
    print("⏳ Warte auf Backend...")
    time.sleep(3)
    
    # Teste Dienstleister
    dienstleister_success = debug_api_milestones()
    
    # Teste Bauträger zum Vergleich
    bautraeger_success = test_bautraeger_comparison()
    
    print("\n" + "=" * 60)
    print("📊 Debug-Ergebnisse:")
    print(f"  Dienstleister-Test: {'✅ Erfolgreich' if dienstleister_success else '❌ Fehlgeschlagen'}")
    print(f"  Bauträger-Test: {'✅ Erfolgreich' if bautraeger_success else '❌ Fehlgeschlagen'}")

if __name__ == "__main__":
    main() 