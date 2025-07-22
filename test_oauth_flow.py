#!/usr/bin/env python3
"""
Test-Skript für den OAuth-Flow
"""

import asyncio
import aiohttp
from app.core.config import settings

async def test_oauth_flow():
    """Testet den OAuth-Flow"""
    
    print("🔍 OAuth-Flow Test")
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
                    print(f"\n📝 Anleitung:")
                    print(f"  1. Öffnen Sie diese URL in Ihrem Browser")
                    print(f"  2. Melden Sie sich bei Microsoft an")
                    print(f"  3. Sie werden zu http://localhost:5173/auth/microsoft/callback weitergeleitet")
                    print(f"  4. Der Callback sollte jetzt funktionieren")
                    print(f"\n⚠️  WICHTIG:")
                    print(f"  - Verwenden Sie die URL nur EINMAL")
                    print(f"  - Jeder Code kann nur EINMAL verwendet werden")
                    print(f"  - Bei Fehlern: Starten Sie den Login-Prozess erneut")
                else:
                    print(f"❌ Fehler beim Generieren der OAuth URL: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ API-Test fehlgeschlagen: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_oauth_flow()) 