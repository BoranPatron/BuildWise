#!/usr/bin/env python3
"""
Test-Skript für Dokumente-API
"""

import requests
import json
from datetime import datetime

def test_documents_api():
    """Testet die Dokumente-API"""
    base_url = "http://localhost:8000"
    
    try:
        print("🔍 Teste Dokumente-API...")
        
        # Test 1: Geo-Suche um Trades mit Dokumenten zu finden
        print("\n1. Teste Geo-Suche...")
        
        geo_data = {
            "latitude": 47.3769,  # Zürich Koordinaten
            "longitude": 8.5417,
            "radius_km": 50,
            "limit": 10
        }
        
        response = requests.post(f"{base_url}/geo/search-trades", json=geo_data)
        
        if response.status_code == 200:
            trades = response.json()
            print(f"✅ Gefunden: {len(trades)} Trades")
            
            # Suche nach Trades mit Dokumenten
            trades_with_docs = [trade for trade in trades if trade.get('documents') and len(trade['documents']) > 0]
            
            print(f"📄 Trades mit Dokumenten: {len(trades_with_docs)}")
            
            if trades_with_docs:
                for trade in trades_with_docs:
                    print(f"\n📋 Trade: {trade['title']} (ID: {trade['id']})")
                    print(f"   📄 Dokumente: {len(trade['documents'])}")
                    
                    for doc in trade['documents']:
                        print(f"      - {doc['name']} ({doc['type']})")
                        print(f"        URL: {doc['url']}")
                        print(f"        Größe: {doc['size']} bytes")
            else:
                print("❌ Keine Trades mit Dokumenten gefunden!")
                
                # Zeige alle Trades ohne Dokumente
                print("\n📋 Alle gefundenen Trades:")
                for trade in trades[:3]:  # Nur erste 3 anzeigen
                    docs = trade.get('documents', [])
                    print(f"   - {trade['title']} (ID: {trade['id']}) - Dokumente: {len(docs)}")
                    
        else:
            print(f"❌ API-Fehler: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Fehler beim Testen der API: {e}")

if __name__ == "__main__":
    test_documents_api() 