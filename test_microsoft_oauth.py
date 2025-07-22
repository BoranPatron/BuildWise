#!/usr/bin/env python3
"""
Microsoft OAuth Debug-Skript
Testet die Microsoft OAuth-Konfiguration
"""

import asyncio
import aiohttp
from app.core.config import settings
from app.services.oauth_service import OAuthService

async def test_microsoft_oauth_config():
    """Testet die Microsoft OAuth-Konfiguration"""
    
    print("🔍 Microsoft OAuth-Konfiguration testen...")
    print("=" * 50)
    
    # 1. Konfiguration prüfen
    print("📋 Konfiguration:")
    print(f"  - Client ID: {settings.microsoft_client_id}")
    print(f"  - Client Secret: {'*' * 10 if settings.microsoft_client_secret else 'Nicht gesetzt'}")
    print(f"  - Redirect URI: {settings.microsoft_redirect_uri}")
    
    if not settings.microsoft_client_id:
        print("❌ Microsoft Client ID nicht konfiguriert!")
        return False
    
    if not settings.microsoft_client_secret:
        print("❌ Microsoft Client Secret nicht konfiguriert!")
        return False
    
    # 2. OAuth URL generieren
    try:
        oauth_url = await OAuthService.get_oauth_url("microsoft")
        print(f"✅ OAuth URL generiert: {oauth_url}")
    except Exception as e:
        print(f"❌ Fehler beim Generieren der OAuth URL: {e}")
        return False
    
    # 3. API-Endpunkt testen
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/api/v1/auth/oauth/microsoft/url") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ API-Endpunkt funktioniert: {data}")
                else:
                    print(f"❌ API-Endpunkt Fehler: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ API-Test fehlgeschlagen: {e}")
        return False
    
    print("✅ Microsoft OAuth-Konfiguration ist korrekt!")
    return True

if __name__ == "__main__":
    asyncio.run(test_microsoft_oauth_config()) 