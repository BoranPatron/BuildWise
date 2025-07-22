#!/usr/bin/env python3
"""
Detailliertes Microsoft OAuth Debug-Skript
Analysiert das 400-Fehler-Problem
"""

import asyncio
import aiohttp
import sys
import os

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def debug_microsoft_oauth_detailed():
    """Detaillierte Analyse des Microsoft OAuth-Problems"""
    
    print("🔍 Detaillierte Microsoft OAuth-Analyse")
    print("=" * 50)
    
    try:
        from app.core.config import settings
        from app.services.oauth_service import OAuthService
        
        # 1. Konfiguration prüfen
        print("📋 1. Konfiguration prüfen:")
        print(f"   - Microsoft Client ID: {settings.microsoft_client_id}")
        print(f"   - Microsoft Client Secret: {'*' * 10 if settings.microsoft_client_secret else 'NICHT GESETZT'}")
        print(f"   - Microsoft Redirect URI: {settings.microsoft_redirect_uri}")
        
        if not settings.microsoft_client_id:
            print("❌ Microsoft Client ID ist nicht konfiguriert!")
            return False
            
        if not settings.microsoft_client_secret:
            print("❌ Microsoft Client Secret ist nicht konfiguriert!")
            return False
        
        # 2. OAuth URL generieren
        print("\n📋 2. OAuth URL generieren:")
        try:
            oauth_url = await OAuthService.get_oauth_url("microsoft")
            print(f"   ✅ OAuth URL generiert: {oauth_url}")
        except Exception as e:
            print(f"   ❌ Fehler beim Generieren der OAuth URL: {e}")
            return False
        
        # 3. Backend-Server testen
        print("\n📋 3. Backend-Server testen:")
        try:
            async with aiohttp.ClientSession() as session:
                # Teste Basis-URL
                async with session.get("http://localhost:8000/") as response:
                    print(f"   - Basis-URL Status: {response.status}")
                
                # Teste API-Docs
                async with session.get("http://localhost:8000/docs") as response:
                    print(f"   - API-Docs Status: {response.status}")
                
                # Teste Microsoft OAuth URL-Endpunkt
                async with session.get("http://localhost:8000/api/v1/auth/oauth/microsoft/url") as response:
                    print(f"   - Microsoft OAuth URL Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"   - Response: {data}")
                    else:
                        error_text = await response.text()
                        print(f"   - Error Response: {error_text}")
                        
                        # Versuche andere Endpunkte
                        print("\n📋 4. Alternative Endpunkte testen:")
                        
                        # Teste ohne /api/v1/
                        async with session.get("http://localhost:8000/auth/oauth/microsoft/url") as response2:
                            print(f"   - Ohne /api/v1/ Status: {response2.status}")
                        
                        # Teste mit /api/
                        async with session.get("http://localhost:8000/api/auth/oauth/microsoft/url") as response3:
                            print(f"   - Mit /api/ Status: {response3.status}")
                        
                        # Teste Google OAuth zum Vergleich
                        async with session.get("http://localhost:8000/api/v1/auth/oauth/google/url") as response4:
                            print(f"   - Google OAuth Status: {response4.status}")
                
        except Exception as e:
            print(f"   ❌ Backend-Test fehlgeschlagen: {e}")
            return False
        
        # 5. Router-Konfiguration prüfen
        print("\n📋 5. Router-Konfiguration prüfen:")
        try:
            from app.main import app
            routes = []
            for route in app.routes:
                if hasattr(route, 'path'):
                    routes.append(f"{route.methods} {route.path}")
            
            print("   Verfügbare Routen:")
            for route in routes[:10]:  # Zeige nur die ersten 10
                print(f"   - {route}")
                
        except Exception as e:
            print(f"   ❌ Router-Analyse fehlgeschlagen: {e}")
        
        print("\n✅ Detaillierte Analyse abgeschlossen!")
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei der Analyse: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_backend_health():
    """Testet die Backend-Gesundheit"""
    
    print("\n🔍 Backend-Gesundheit testen:")
    print("=" * 30)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Teste verschiedene Endpunkte
            endpoints = [
                "http://localhost:8000/",
                "http://localhost:8000/docs",
                "http://localhost:8000/openapi.json",
                "http://localhost:8000/api/v1/",
                "http://localhost:8000/api/v1/auth/",
                "http://localhost:8000/api/v1/auth/oauth/",
                "http://localhost:8000/api/v1/auth/oauth/microsoft/",
                "http://localhost:8000/api/v1/auth/oauth/microsoft/url"
            ]
            
            for endpoint in endpoints:
                try:
                    async with session.get(endpoint) as response:
                        print(f"   {endpoint}: {response.status}")
                except Exception as e:
                    print(f"   {endpoint}: ERROR - {e}")
                    
    except Exception as e:
        print(f"❌ Backend-Gesundheit-Test fehlgeschlagen: {e}")

async def main():
    """Hauptfunktion"""
    print("🧪 Microsoft OAuth detaillierte Analyse")
    print("=" * 50)
    
    # Detaillierte Analyse
    success = await debug_microsoft_oauth_detailed()
    
    if not success:
        print("\n🔍 Backend-Gesundheit prüfen...")
        await test_backend_health()
    
    print("\n💡 Empfehlungen:")
    print("   1. Prüfen Sie, ob der Backend-Server läuft")
    print("   2. Prüfen Sie die .env-Konfiguration")
    print("   3. Prüfen Sie die Router-Konfiguration")
    print("   4. Testen Sie mit einem anderen Browser")

if __name__ == "__main__":
    asyncio.run(main()) 