#!/usr/bin/env python3
"""
Test-Skript für BuildWise-Gebühren-API-Aufruf
"""

import asyncio
import sys
import os
import aiohttp
import json

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_api_call():
    """Testet den BuildWise-Gebühren-API-Aufruf"""
    
    url = "http://localhost:8000/api/v1/buildwise-fees/create-from-quote/1/1"
    params = {"fee_percentage": 4.0}
    
    print(f"🚀 Teste API-Aufruf: {url}")
    print(f"📋 Parameter: {params}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as response:
                print(f"📊 Status: {response.status}")
                print(f"📋 Headers: {dict(response.headers)}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Erfolg: {json.dumps(data, indent=2)}")
                else:
                    error_text = await response.text()
                    print(f"❌ Fehler {response.status}: {error_text}")
                    
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("🚀 Teste BuildWise-Gebühren-API...")
    asyncio.run(test_api_call())
    print("✅ Fertig!") 