#!/usr/bin/env python3
"""
Umfassender Test für Microsoft OAuth-Konfiguration
"""

import asyncio
import aiohttp
import json
from urllib.parse import urlencode

async def test_microsoft_oauth_configuration():
    """Testet die Microsoft OAuth-Konfiguration"""
    
    print("🔧 Teste Microsoft OAuth-Konfiguration...")
    
    try:
        # Importiere Settings
        from app.core.config import settings
        
        print("✅ Settings geladen")
        print(f"   - Microsoft Client ID: {settings.microsoft_client_id}")
        print(f"   - Microsoft Client Secret: {'✅ Konfiguriert' if settings.microsoft_client_secret else '❌ Fehlt'}")
        print(f"   - Microsoft Redirect URI: {settings.microsoft_redirect_uri}")
        
        if not settings.microsoft_client_id or not settings.microsoft_client_secret:
            print("❌ Microsoft OAuth ist nicht vollständig konfiguriert")
            return False
            
        print("✅ Microsoft OAuth ist vollständig konfiguriert!")
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Laden der Settings: {e}")
        return False

async def test_microsoft_oauth_url_generation():
    """Testet die Generierung der Microsoft OAuth-URL"""
    
    print("\n🔧 Teste Microsoft OAuth-URL-Generierung...")
    
    try:
        from app.services.oauth_service import OAuthService
        
        # Generiere OAuth-URL
        oauth_url = await OAuthService.get_oauth_url("microsoft")
        
        print("✅ OAuth-URL erfolgreich generiert")
        print(f"   - URL: {oauth_url[:100]}...")
        
        # Prüfe URL-Parameter
        if "login.microsoftonline.com" in oauth_url and "client_id=" in oauth_url:
            print("✅ URL enthält korrekte Microsoft-Parameter")
            return True
        else:
            print("❌ URL enthält nicht die erwarteten Parameter")
            return False
            
    except Exception as e:
        print(f"❌ Fehler bei der OAuth-URL-Generierung: {e}")
        return False

async def test_backend_oauth_endpoint():
    """Testet den Backend OAuth-Endpunkt"""
    
    print("\n🔧 Teste Backend OAuth-Endpunkt...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Teste OAuth-URL-Endpunkt
            url = "http://localhost:8000/api/v1/auth/oauth/microsoft/url"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Backend OAuth-Endpunkt funktioniert")
                    print(f"   - OAuth URL: {data.get('oauth_url', 'N/A')[:100]}...")
                    return True
                else:
                    print(f"❌ Backend OAuth-Endpunkt fehlgeschlagen: {response.status}")
                    error_text = await response.text()
                    print(f"   - Fehler: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Fehler beim Testen des Backend-Endpunkts: {e}")
        return False

async def test_frontend_oauth_integration():
    """Testet die Frontend OAuth-Integration"""
    
    print("\n🔧 Teste Frontend OAuth-Integration...")
    
    try:
        # Simuliere Frontend-Request
        async with aiohttp.ClientSession() as session:
            # Teste Frontend-Request an Backend
            url = "http://localhost:8000/api/v1/auth/oauth/microsoft/url"
            headers = {
                "Content-Type": "application/json",
                "Origin": "http://localhost:5173"
            }
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Frontend-Integration funktioniert")
                    print(f"   - CORS-Header: {dict(response.headers)}")
                    return True
                else:
                    print(f"❌ Frontend-Integration fehlgeschlagen: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Fehler bei der Frontend-Integration: {e}")
        return False

async def test_microsoft_graph_api():
    """Testet die Microsoft Graph API (mit Mock-Token)"""
    
    print("\n🔧 Teste Microsoft Graph API...")
    
    try:
        # Simuliere Token-Austausch (ohne echten Code)
        from app.services.oauth_service import OAuthService
        
        # Teste User-Info-Abruf mit Mock-Token
        mock_token = "mock_access_token_for_testing"
        user_info = await OAuthService.get_microsoft_user_info(mock_token)
        
        if user_info is None:
            print("✅ Microsoft Graph API-Test (erwartetes Verhalten für Mock-Token)")
            return True
        else:
            print("⚠️ Unerwartetes Ergebnis bei Mock-Token")
            return False
            
    except Exception as e:
        print(f"❌ Fehler beim Microsoft Graph API-Test: {e}")
        return False

async def main():
    """Hauptfunktion für alle Tests"""
    
    print("🚀 Starte umfassende Microsoft OAuth-Tests...")
    print("=" * 60)
    
    tests = [
        ("Konfiguration", test_microsoft_oauth_configuration),
        ("OAuth-URL-Generierung", test_microsoft_oauth_url_generation),
        ("Backend-Endpunkt", test_backend_oauth_endpoint),
        ("Frontend-Integration", test_frontend_oauth_integration),
        ("Graph API", test_microsoft_graph_api)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' fehlgeschlagen: {e}")
            results.append((test_name, False))
    
    # Zusammenfassung
    print("\n" + "=" * 60)
    print("📊 TEST-ZUSAMMENFASSUNG")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ BESTANDEN" if result else "❌ FEHLGESCHLAGEN"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1
    
    print(f"\nErgebnis: {passed}/{total} Tests bestanden")
    
    if passed == total:
        print("🎉 Alle Tests bestanden! Microsoft OAuth ist vollständig konfiguriert.")
        print("\n🚀 Nächste Schritte:")
        print("1. Starten Sie den Backend-Server:")
        print("   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("2. Testen Sie Microsoft OAuth im Frontend")
        print("3. Überprüfen Sie die Azure App-Registrierung")
    else:
        print("⚠️ Einige Tests fehlgeschlagen. Überprüfen Sie die Konfiguration.")
        print("\n🔧 Empfohlene Schritte:")
        print("1. Überprüfen Sie die .env-Datei")
        print("2. Starten Sie den Backend-Server neu")
        print("3. Überprüfen Sie die Azure App-Registrierung")

if __name__ == "__main__":
    asyncio.run(main()) 