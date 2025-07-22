#!/usr/bin/env python3
"""
Debug-Skript für Microsoft OAuth-Probleme
"""

import asyncio
import aiohttp
from app.core.config import settings

async def debug_microsoft_oauth():
    """Debuggt Microsoft OAuth-Probleme"""
    
    print("🔍 Microsoft OAuth Debug")
    print("=" * 50)
    
    # 1. Prüfe Konfiguration
    print("📋 Konfiguration:")
    print(f"  - Client ID: {settings.microsoft_client_id}")
    print(f"  - Client Secret: {'*' * 10 if settings.microsoft_client_secret else 'Nicht gesetzt'}")
    print(f"  - Redirect URI: {settings.microsoft_redirect_uri}")
    
    if not settings.microsoft_client_id or not settings.microsoft_client_secret:
        print("❌ Microsoft OAuth nicht vollständig konfiguriert!")
        return False
    
    # 2. Teste OAuth URL Generation
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/api/v1/auth/oauth/microsoft/url") as response:
                if response.status == 200:
                    data = await response.json()
                    oauth_url = data.get('oauth_url')
                    print(f"✅ OAuth URL generiert:")
                    print(f"  {oauth_url}")
                else:
                    print(f"❌ OAuth URL Generation fehlgeschlagen: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ OAuth URL Test fehlgeschlagen: {e}")
        return False
    
    print("\n📝 Nächste Schritte:")
    print("   1. Öffnen Sie die OAuth URL in Ihrem Browser")
    print("   2. Melden Sie sich bei Microsoft an")
    print("   3. Schauen Sie in die Backend-Logs für Debug-Informationen")
    print("   4. Prüfen Sie die Microsoft Graph API-Antworten")
    
    return True

if __name__ == "__main__":
    asyncio.run(debug_microsoft_oauth()) 