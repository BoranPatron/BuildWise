#!/usr/bin/env python3
"""
Teste die vereinfachte Archiv-API
"""

import requests
import json

def test_simple_archive():
    try:
        # Teste die vereinfachte API
        url = "http://localhost:8000/api/v1/milestones/archived"
        
        print(f"🔍 Teste API: {url}")
        
        # Test ohne Parameter
        response = requests.get(url)
        print(f"Status ohne Parameter: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Erfolgreich! {len(data)} archivierte Gewerke gefunden")
            if data:
                print(f"Erstes Gewerk: {data[0]['title']}")
        else:
            print(f"❌ Fehler: {response.text}")
        
        print()
        
        # Test mit project_id
        response = requests.get(f"{url}?project_id=1")
        print(f"Status mit project_id=1: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Erfolgreich! {len(data)} archivierte Gewerke für Projekt 1 gefunden")
        else:
            print(f"❌ Fehler: {response.text}")
            
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    test_simple_archive()
