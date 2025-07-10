#!/usr/bin/env python3
"""
Listet alle Milestones und die zugehörigen Angebote für den Dienstleister "Boran GmBh" auf.
"""
import requests

BASE_URL = "http://localhost:8000/api/v1"
LOGIN_URL = f"{BASE_URL}/auth/login"

USERNAME = "test-dienstleister@buildwise.de"
PASSWORD = "test1234"

def login():
    resp = requests.post(LOGIN_URL, data={"username": USERNAME, "password": PASSWORD})
    resp.raise_for_status()
    return resp.json()["access_token"]

def list_milestones_and_quotes(token):
    headers = {"Authorization": f"Bearer {token}"}
    ms_resp = requests.get(f"{BASE_URL}/milestones/all", headers=headers)
    ms_resp.raise_for_status()
    milestones = ms_resp.json()
    print("\n--- Alle Milestones ---")
    for m in milestones:
        print(f"{m['id']}: {m['title']}")
    print("\n--- Angebote pro Milestone ---")
    for m in milestones:
        quotes_resp = requests.get(f"{BASE_URL}/quotes/milestone/{m['id']}", headers=headers)
        quotes_resp.raise_for_status()
        quotes = quotes_resp.json()
        print(f"\nMilestone {m['id']} ({m['title']}): {len(quotes)} Angebote")
        for q in quotes:
            print(f"  - Angebot ID: {q['id']}, Titel: {q.get('title')}, Firma: {q.get('company_name')}, Status: {q.get('status')}")

def main():
    token = login()
    list_milestones_and_quotes(token)

if __name__ == "__main__":
    main() 