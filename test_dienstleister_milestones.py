#!/usr/bin/env python3
"""
Test-Skript für Dienstleister-Milestones nach dem Öffentlich-Machen des Projekts
"""

import requests
import json
import time

# API-Konfiguration
BASE_URL = "http://localhost:8000/api/v1"
LOGIN_URL = f"{BASE_URL}/auth/login"
MILESTONES_URL = f"{BASE_URL}/milestones/all"

def test_dienstleister_login_and_milestones():
    """Testet Dienstleister-Login und Milestone-Abruf"""
    
    print("🔍 Teste Dienstleister-Login und Milestones")
    print("=" * 50)
    
    # Login-Daten für Dienstleister (form-data Format)
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
        print(f"  Token: {token[:20]}...")
        
        # 2. Milestones abrufen
        print("\n📋 Rufe Milestones ab...")
        headers = {"Authorization": f"Bearer {token}"}
        milestones_response = requests.get(MILESTONES_URL, headers=headers)
        
        if milestones_response.status_code != 200:
            print(f"❌ Milestones-Abruf fehlgeschlagen: {milestones_response.status_code}")
            print(f"Response: {milestones_response.text}")
            return False
        
        milestones = milestones_response.json()
        print(f"✅ Milestones erfolgreich abgerufen!")
        print(f"  Anzahl Milestones: {len(milestones)}")
        
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
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Verbindung zum Backend fehlgeschlagen")
        print("💡 Stellen Sie sicher, dass das Backend läuft: python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Fehler beim Testen: {e}")
        return False

def test_bautraeger_milestones_for_comparison():
    """Testet Bauträger-Login zum Vergleich"""
    
    print("\n🔍 Vergleich: Bauträger-Milestones")
    print("=" * 50)
    
    # Login-Daten für Bauträger (form-data Format)
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
        
        if len(milestones) > 0:
            print("\n📋 Gefundene Milestones (Bauträger):")
            for i, milestone in enumerate(milestones, 1):
                print(f"  {i}. ID: {milestone.get('id')}")
                print(f"     Titel: {milestone.get('title')}")
                print(f"     Status: {milestone.get('status')}")
                print(f"     Projekt-ID: {milestone.get('project_id')}")
                print()
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Bauträger-Test: {e}")
        return False

def main():
    """Hauptfunktion"""
    print("🧪 Dienstleister-Milestones Test")
    print("=" * 60)
    print(f"⏰ Zeitstempel: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Warte kurz, damit das Backend starten kann
    print("⏳ Warte auf Backend...")
    time.sleep(3)
    
    # Teste Dienstleister
    dienstleister_success = test_dienstleister_login_and_milestones()
    
    # Teste Bauträger zum Vergleich
    bautraeger_success = test_bautraeger_milestones_for_comparison()
    
    print("\n" + "=" * 60)
    print("📊 Test-Ergebnisse:")
    print(f"  Dienstleister-Test: {'✅ Erfolgreich' if dienstleister_success else '❌ Fehlgeschlagen'}")
    print(f"  Bauträger-Test: {'✅ Erfolgreich' if bautraeger_success else '❌ Fehlgeschlagen'}")
    
    if dienstleister_success:
        print("\n🎉 Problem gelöst! Dienstleister können jetzt Milestones sehen.")
    else:
        print("\n⚠️  Problem besteht noch. Überprüfen Sie die Backend-Logs.")

if __name__ == "__main__":
    main() 