#!/usr/bin/env python3
"""
HTTP-Test für das Backend
"""

import requests
import time
import sys

def test_backend_http():
    """Testet das Backend über HTTP"""
    print("🔍 HTTP-BACKEND-TEST")
    print("=" * 25)
    
    base_url = "http://localhost:8000"
    
    # Warte kurz, bis das Backend startet
    print("⏳ Warte auf Backend...")
    time.sleep(2)
    
    try:
        # Teste Root-Endpoint
        print("🔧 Teste Root-Endpoint...")
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"✅ Root-Status: {response.status_code}")
        print(f"📄 Root-Response: {response.json()}")
        
        # Teste Health-Endpoint
        print("\n🔧 Teste Health-Endpoint...")
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Health-Status: {response.status_code}")
        print(f"📄 Health-Response: {response.json()}")
        
        # Teste API-Dokumentation
        print("\n🔧 Teste API-Dokumentation...")
        response = requests.get(f"{base_url}/docs", timeout=5)
        print(f"✅ Docs-Status: {response.status_code}")
        
        print("\n✅ Backend-HTTP-Test erfolgreich!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Backend nicht erreichbar - läuft es?")
        return False
    except Exception as e:
        print(f"❌ HTTP-Test-Fehler: {e}")
        return False

if __name__ == "__main__":
    success = test_backend_http()
    if success:
        print("\n🎉 Backend ist bereit!")
    else:
        print("\n💥 Backend-Test fehlgeschlagen!")
        sys.exit(1) 