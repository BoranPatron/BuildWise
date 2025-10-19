#!/usr/bin/env python3
import requests
import json

def test_notifications_api():
    # Simuliere einen Login um ein Token zu bekommen
    login_url = "http://localhost:8000/api/v1/auth/login"
    login_data = {
        "username": "s.schellworth@valueon.ch",
        "password": "password123"  # Das ist wahrscheinlich das Standard-Passwort
    }
    
    try:
        print("🔄 Versuche Login...")
        login_response = requests.post(login_url, data=login_data)
        print(f"Login Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            token = token_data.get('access_token')
            print(f"✅ Token erhalten: {token[:50]}...")
            
            # Teste Notifications API mit Token
            notifications_url = "http://localhost:8000/api/v1/notifications/"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            print("🔄 Teste Notifications API...")
            notif_response = requests.get(notifications_url, headers=headers)
            print(f"Notifications Status: {notif_response.status_code}")
            
            if notif_response.status_code == 200:
                notifications = notif_response.json()
                print(f"✅ {len(notifications)} Benachrichtigungen gefunden:")
                for notif in notifications:
                    print(f"  - ID: {notif['id']}, Type: {notif['type']}, Title: {notif['title']}")
            else:
                print(f"❌ Notifications API Fehler: {notif_response.text}")
        else:
            print(f"❌ Login fehlgeschlagen: {login_response.text}")
            
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    test_notifications_api()
