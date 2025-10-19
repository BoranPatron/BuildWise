#!/usr/bin/env python3
"""
Einfacher Test für den Company Logo Endpoint
"""

import requests
import json

def test_endpoint():
    BASE_URL = "http://localhost:8000"
    USER_ID = 2
    
    print("Teste Company Logo Endpoint...")
    
    # 1. Teste ohne Authentifizierung
    response = requests.get(f"{BASE_URL}/api/v1/users/{USER_ID}/company-logo")
    print(f"Status ohne Auth: {response.status_code}")
    
    if response.status_code == 401:
        print("✅ Endpoint existiert (401 = Unauthorized)")
    elif response.status_code == 404:
        print("❌ Endpoint existiert nicht (404 = Not Found)")
    else:
        print(f"⚠️ Unerwarteter Status: {response.status_code}")
    
    # 2. Teste mit einem einfachen Token (falls vorhanden)
    try:
        # Versuche einen Test-Token zu verwenden
        headers = {"Authorization": "Bearer test-token"}
        response = requests.get(f"{BASE_URL}/api/v1/users/{USER_ID}/company-logo", headers=headers)
        print(f"Status mit Test-Token: {response.status_code}")
    except Exception as e:
        print(f"Fehler beim Test mit Token: {e}")

if __name__ == "__main__":
    test_endpoint()
