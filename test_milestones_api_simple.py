#!/usr/bin/env python3
"""
Einfaches Test-Skript für die Milestones-API
"""

import requests
import json

def test_milestones_api():
    """Testet die Milestones-API"""
    base_url = "http://localhost:8000/api/v1"
    
    try:
        # Teste GET /milestones mit project_id
        print("🔧 Teste GET /milestones...")
        response = requests.get(
            f"{base_url}/milestones?project_id=1",
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Erfolgreich! {len(data)} Milestones gefunden")
            for milestone in data:
                print(f"  • {milestone.get('title', 'N/A')} (ID: {milestone.get('id', 'N/A')})")
        else:
            print(f"❌ Fehler: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Verbindung zum Server fehlgeschlagen. Ist der Server gestartet?")
    except Exception as e:
        print(f"❌ Fehler: {e}")


def test_milestones_all():
    """Testet GET /milestones/all"""
    base_url = "http://localhost:8000/api/v1"
    
    try:
        print("\n🔧 Teste GET /milestones/all...")
        response = requests.get(
            f"{base_url}/milestones/all",
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Erfolgreich! {len(data)} Milestones gefunden")
            for milestone in data:
                print(f"  • {milestone.get('title', 'N/A')} (ID: {milestone.get('id', 'N/A')})")
        else:
            print(f"❌ Fehler: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Verbindung zum Server fehlgeschlagen. Ist der Server gestartet?")
    except Exception as e:
        print(f"❌ Fehler: {e}")


if __name__ == "__main__":
    print("🧪 Teste Milestones-API...")
    print("=" * 50)
    
    test_milestones_api()
    test_milestones_all() 