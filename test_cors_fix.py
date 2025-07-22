#!/usr/bin/env python3
"""
Test-Skript für CORS-Behebung
"""

import asyncio
import aiohttp

async def test_cors_fix():
    """Testet die CORS-Konfiguration"""
    
    print("🔍 CORS-Test für Microsoft OAuth")
    print("=" * 50)
    
    # 1. Teste OPTIONS-Request (Preflight)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.options("http://localhost:8000/api/v1/auth/oauth/microsoft/callback") as response:
                print(f"✅ OPTIONS-Request Status: {response.status}")
                print(f"  - Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin', 'Nicht gesetzt')}")
                print(f"  - Access-Control-Allow-Methods: {response.headers.get('Access-Control-Allow-Methods', 'Nicht gesetzt')}")
                print(f"  - Access-Control-Allow-Headers: {response.headers.get('Access-Control-Allow-Headers', 'Nicht gesetzt')}")
    except Exception as e:
        print(f"❌ OPTIONS-Test fehlgeschlagen: {e}")
    
    # 2. Teste POST-Request (mit Dummy-Daten)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8000/api/v1/auth/oauth/microsoft/callback",
                json={"code": "test_code", "state": None},
                headers={"Content-Type": "application/json"}
            ) as response:
                print(f"✅ POST-Request Status: {response.status}")
                print(f"  - Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin', 'Nicht gesetzt')}")
                response_text = await response.text()
                print(f"  - Response: {response_text[:100]}...")
    except Exception as e:
        print(f"❌ POST-Test fehlgeschlagen: {e}")
    
    print("\n📝 Nächste Schritte:")
    print("   1. Frontend neu laden")
    print("   2. Microsoft OAuth erneut testen")
    print("   3. Browser-Entwicklertools prüfen")

if __name__ == "__main__":
    asyncio.run(test_cors_fix()) 