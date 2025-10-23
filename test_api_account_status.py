#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test API-Call für Account-Status Check
"""
import requests
import json
import sys

# Fix encoding für Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# API-Konfiguration
BASE_URL = "http://localhost:8000/api/v1"

# Token aus localStorage (muss manuell eingefügt werden)
# Oder: Login durchführen
print("=" * 60)
print("API ACCOUNT STATUS TEST")
print("=" * 60)

# Test 1: Login als Dienstleister
print("\n1. Login als Dienstleister (janina.hankus@momentumvisuals.de)...")
login_data = {
    "username": "janina.hankus@momentumvisuals.de",
    "password": "test123"  # Ändere dies zum echten Passwort
}

try:
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data=login_data
    )
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"   Login erfolgreich! Token: {token[:20]}...")
        
        # Test 2: Check Account Status
        print("\n2. Check Account Status...")
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        status_response = requests.get(
            f"{BASE_URL}/buildwise-fees/check-account-status",
            headers=headers
        )
        
        print(f"   Status Code: {status_response.status_code}")
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            print("\n" + "=" * 60)
            print("ACCOUNT STATUS RESPONSE:")
            print("=" * 60)
            print(json.dumps(status_data, indent=2, ensure_ascii=False))
            print("=" * 60)
            
            if status_data.get("account_locked"):
                print("\n>>> ACCOUNT IST GESPERRT <<<")
                print(f"Ueberfaellige Gebuehren: {len(status_data.get('overdue_fees', []))}")
                print(f"Gesamtbetrag: {status_data.get('total_overdue_amount')} EUR")
            else:
                print("\n>>> ACCOUNT IST NICHT GESPERRT <<<")
                print("Problem: Account sollte gesperrt sein!")
        else:
            print(f"   Fehler: {status_response.text}")
    else:
        print(f"   Login fehlgeschlagen: {response.status_code}")
        print(f"   Response: {response.text}")

except Exception as e:
    print(f"Fehler: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test abgeschlossen")
print("=" * 60)


