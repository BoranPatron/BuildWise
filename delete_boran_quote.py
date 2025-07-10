#!/usr/bin/env python3
"""
Skript zum gezielten Löschen eines Angebots mit einer bestimmten ID (hier: 1)
"""
import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"
LOGIN_URL = f"{BASE_URL}/auth/login"
USERNAME = "test-dienstleister@buildwise.de"
PASSWORD = "test1234"
QUOTE_ID = 1

def login():
    resp = requests.post(LOGIN_URL, data={"username": USERNAME, "password": PASSWORD})
    resp.raise_for_status()
    return resp.json()["access_token"]

def delete_quote(token, quote_id):
    headers = {"Authorization": f"Bearer {token}"}
    print(f"🗑️ Lösche gezielt Angebot ID: {quote_id}")
    resp = requests.delete(f"{BASE_URL}/quotes/{quote_id}", headers=headers)
    if resp.status_code == 200:
        print("✅ Angebot erfolgreich gelöscht!")
        return True
    else:
        print(f"❌ Fehler beim Löschen: {resp.status_code}")
        print(f"Antwort: {resp.text}")
        return False

def main():
    print(f"🚀 Starte gezielte Löschung von Angebot ID {QUOTE_ID} ...")
    token = login()
    success = delete_quote(token, QUOTE_ID)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main() 