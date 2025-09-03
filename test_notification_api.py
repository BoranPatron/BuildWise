#!/usr/bin/env python3
import requests
import json

def test_notification_api():
    url = "http://localhost:8000/api/v1/notifications/"
    
    notification_data = {
        "recipient_id": 77,
        "type": "quote_accepted",
        "title": "Angebot angenommen",
        "message": "Ihr Angebot für 'Sanitär- und Heizungsinstallation' wurde vom Bauträger angenommen. Sie können nun mit der Ausführung beginnen.",
        "priority": "high",
        "related_quote_id": 1,
        "related_project_id": 1,
        "related_milestone_id": 1
    }
    
    try:
        print("🔄 Teste Benachrichtigungs-API...")
        response = requests.post(url, json=notification_data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Benachrichtigung erfolgreich erstellt!")
        else:
            print(f"❌ Fehler beim Erstellen der Benachrichtigung: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Netzwerk-Fehler: {e}")

if __name__ == "__main__":
    test_notification_api()