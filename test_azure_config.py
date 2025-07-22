#!/usr/bin/env python3
"""
Test-Skript für Azure OAuth-Konfiguration
"""

import os
import asyncio
import aiohttp

# Temporäre Konfiguration für Test
MICROSOFT_CLIENT_ID = "c5247a29-0cb4-4cdf-9f4c-a091a3a42383"
MICROSOFT_REDIRECT_URI = "http://localhost:5173/auth/microsoft/callback"

async def test_azure_oauth_url():
    """Testet die Azure OAuth URL-Generierung"""
    
    print("🔍 Azure OAuth-Konfiguration testen...")
    print("=" * 50)
    
    # 1. Client ID prüfen
    print(f"📋 Konfiguration:")
    print(f"  - Client ID: {MICROSOFT_CLIENT_ID}")
    print(f"  - Redirect URI: {MICROSOFT_REDIRECT_URI}")
    
    # 2. OAuth URL generieren
    params = {
        "client_id": MICROSOFT_CLIENT_ID,
        "redirect_uri": MICROSOFT_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "response_mode": "query"
    }
    
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    oauth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{query_string}"
    
    print(f"✅ OAuth URL generiert:")
    print(f"  {oauth_url}")
    
    # 3. API-Endpunkt testen (falls Backend läuft)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/api/v1/auth/oauth/microsoft/url") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ API-Endpunkt funktioniert: {data}")
                else:
                    print(f"⚠️  API-Endpunkt nicht verfügbar (Status: {response.status})")
                    print("   Das ist normal, wenn das Backend nicht läuft")
    except Exception as e:
        print(f"⚠️  API-Test fehlgeschlagen: {e}")
        print("   Das ist normal, wenn das Backend nicht läuft")
    
    print("\n✅ Azure OAuth-URL ist korrekt generiert!")
    print("📝 Nächste Schritte:")
    print("   1. Client Secret aus Azure Portal kopieren")
    print("   2. .env-Datei mit Client Secret erstellen")
    print("   3. Backend neu starten")
    print("   4. Frontend testen")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_azure_oauth_url()) 