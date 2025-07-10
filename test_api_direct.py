#!/usr/bin/env python3
"""
Direkter API-Test für /milestones/all
"""

import requests
import json

def test_milestones_api():
    """Testet die /milestones/all API direkt"""
    
    # Neues Token generieren (Login simulieren)
    login_data = {
        'username': 'test-dienstleister@buildwise.de',
        'password': 'test1234'
    }
    
    # Erst Login machen um Token zu bekommen
    login_response = requests.post('http://localhost:8000/api/v1/auth/login', data=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Login fehlgeschlagen: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return
    
    token_data = login_response.json()
    token = token_data['access_token']
    
    print(f"✅ Login erfolgreich, Token erhalten")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = "http://localhost:8000/api/v1/milestones/all"
    
    print("🔍 Teste API direkt...")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.get(url, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Data: {data}")
            print(f"Response Type: {type(data)}")
            print(f"Response Length: {len(data) if isinstance(data, list) else 'N/A'}")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Fehler beim API-Test: {e}")

if __name__ == "__main__":
    test_milestones_api() 