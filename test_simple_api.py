#!/usr/bin/env python3
"""
Einfacher API-Test
"""

import requests
import json

try:
    # Test einfacher GET-Endpunkt
    response = requests.get("http://localhost:8000/")
    print(f"Root endpoint: {response.status_code}")
    
    # Test POST mit Daten
    data = {
        "latitude": 47.3769,
        "longitude": 8.5417,
        "radius_km": 50,
        "limit": 10
    }
    
    response = requests.post("http://localhost:8000/api/v1/geo/search-trades", json=data)
    print(f"Search trades: {response.status_code}")
    
    if response.status_code == 200:
        trades = response.json()
        print(f"Trades gefunden: {len(trades)}")
        
        for trade in trades:
            docs = trade.get('documents', [])
            print(f"  - {trade['title']}: {len(docs)} Dokumente")
            
            if docs:
                for doc in docs:
                    print(f"    * {doc['name']}")
    else:
        print(f"Fehler: {response.text}")
        
except Exception as e:
    print(f"Fehler: {e}") 