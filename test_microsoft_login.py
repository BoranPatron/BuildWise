#!/usr/bin/env python3
"""
Test-Skript für Microsoft OAuth-Login
"""

import asyncio
import aiohttp
from app.core.config import settings

async def test_microsoft_oauth_flow():
    """Testet den Microsoft OAuth-Flow"""
    
    print("🔍 Microsoft OAuth-Login Test")
    print("=" * 50)
    
    # 1. OAuth URL generieren
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/api/v1/auth/oauth/microsoft/url") as response:
                if response.status == 200:
                    data = await response.json()
                    oauth_url = data.get('oauth_url')
                    print(f"✅ OAuth URL generiert:")
                    print(f"  {oauth_url}")
                    print(f"\n📝 Nächste Schritte:")
                    print(f"  1. Öffnen Sie diese URL in Ihrem Browser")
                    print(f"  2. Melden Sie sich bei Microsoft an")
                    print(f"  3. Sie werden zu http://localhost:5173/auth/microsoft/callback weitergeleitet")
                    print(f"  4. Der Callback sollte jetzt funktionieren")
                else:
                    print(f"❌ Fehler beim Generieren der OAuth URL: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ API-Test fehlgeschlagen: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_microsoft_oauth_flow()) 