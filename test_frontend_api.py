#!/usr/bin/env python3
"""
Test-Skript für Frontend-API-Aufruf mit Authentifizierung
"""

import asyncio
import sys
import os
import aiohttp
import json

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_frontend_api():
    """Testet den Frontend-API-Aufruf mit Authentifizierung"""
    
    # Simuliere einen authentifizierten Benutzer
    # In der Praxis würde das Frontend einen gültigen Token haben
    url = "http://localhost:8000/api/v1/buildwise-fees/create-from-quote/1/1"
    params = {"fee_percentage": 4.0}
    
    # Simuliere einen gültigen JWT-Token (in der Praxis vom Frontend)
    headers = {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json"
    }
    
    print(f"🚀 Teste Frontend-API-Aufruf: {url}")
    print(f"📋 Parameter: {params}")
    print(f"🔑 Headers: {headers}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params, headers=headers) as response:
                print(f"📊 Status: {response.status}")
                print(f"📋 Headers: {dict(response.headers)}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Erfolg: {json.dumps(data, indent=2)}")
                elif response.status == 401:
                    print("❌ 401 Unauthorized - Token erforderlich")
                    print("💡 Das ist normal, da wir keinen gültigen Token haben")
                else:
                    error_text = await response.text()
                    print(f"❌ Fehler {response.status}: {error_text}")
                    
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("🚀 Teste Frontend-API-Aufruf...")
    asyncio.run(test_frontend_api())
    print("✅ Fertig!") 