#!/usr/bin/env python3
"""
Debug-Endpoint für Archiv-API um den genauen Fehler zu sehen
"""

import requests
import json

def debug_archive_endpoint():
    try:
        # Teste verschiedene Parameter-Kombinationen
        base_url = "http://localhost:8000/api/v1/milestones/archived"
        
        # Test 1: Ohne Parameter
        print("🔍 Test 1: Ohne Parameter")
        response = requests.get(base_url)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        print()
        
        # Test 2: Mit project_id als String
        print("🔍 Test 2: Mit project_id als String")
        response = requests.get(f"{base_url}?project_id=1")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        print()
        
        # Test 3: Mit project_id als Integer (sollte funktionieren)
        print("🔍 Test 3: Mit project_id als Integer")
        response = requests.get(f"{base_url}?project_id=1&skip=0&limit=100")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        print()
        
        # Test 4: Mit allen Parametern
        print("🔍 Test 4: Mit allen Parametern")
        response = requests.get(f"{base_url}?project_id=1&search_query=&category_filter=all&skip=0&limit=100")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        print()
        
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    debug_archive_endpoint()
