#!/usr/bin/env python3
"""
Schneller Test für Microsoft OAuth-Konfiguration
"""

import sys
import os

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_microsoft_oauth_config():
    """Testet die Microsoft OAuth-Konfiguration"""
    
    print("🔧 Test Microsoft OAuth-Konfiguration")
    print("=" * 50)
    
    try:
        from app.core.config import settings
        from app.services.oauth_service import OAuthService
        import asyncio
        
        print("📋 1. Überprüfe Settings:")
        print(f"   - Microsoft Client ID: {settings.microsoft_client_id}")
        print(f"   - Microsoft Client Secret: {settings.microsoft_client_secret}")
        print(f"   - Microsoft Redirect URI: {settings.microsoft_redirect_uri}")
        
        # Prüfe ob Konfiguration vorhanden ist
        if settings.microsoft_client_id and settings.microsoft_client_id != "your-microsoft-client-id-here":
            print("   ✅ Microsoft Client ID ist konfiguriert")
        else:
            print("   ❌ Microsoft Client ID ist nicht konfiguriert")
        
        if settings.microsoft_client_secret and settings.microsoft_client_secret != "your-microsoft-client-secret-here":
            print("   ✅ Microsoft Client Secret ist konfiguriert")
        else:
            print("   ❌ Microsoft Client Secret ist nicht konfiguriert")
        
        print(f"   ✅ Microsoft Redirect URI ist konfiguriert: {settings.microsoft_redirect_uri}")
        
        # 2. Teste OAuth URL Generation
        print("\n📋 2. Teste OAuth URL Generation:")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            oauth_url = loop.run_until_complete(OAuthService.get_oauth_url("microsoft", "test-state"))
            print(f"   ✅ OAuth URL erfolgreich generiert:")
            print(f"   {oauth_url}")
            loop.close()
        except ValueError as e:
            print(f"   ❌ Fehler bei OAuth URL Generation: {e}")
        
        # 3. Teste Google OAuth (Referenz)
        print("\n📋 3. Teste Google OAuth (Referenz):")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            google_url = loop.run_until_complete(OAuthService.get_oauth_url("google", "test-state"))
            print(f"   ✅ Google OAuth URL erfolgreich generiert:")
            print(f"   {google_url}")
            loop.close()
        except ValueError as e:
            print(f"   ❌ Fehler bei Google OAuth URL Generation: {e}")
        
        print("\n✅ Test abgeschlossen!")
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_microsoft_oauth_config() 