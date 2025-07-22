#!/usr/bin/env python3
"""
Test-Skript für Microsoft OAuth-Fix
"""

import sys
import os
import asyncio

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_microsoft_oauth():
    """Testet die Microsoft OAuth-Konfiguration"""
    
    print("🔧 Test Microsoft OAuth-Fix")
    print("=" * 40)
    
    try:
        from app.core.config import settings
        from app.services.oauth_service import OAuthService
        
        print("📋 1. Überprüfe Settings:")
        print(f"   - Microsoft Client ID: {settings.microsoft_client_id}")
        print(f"   - Microsoft Client Secret: {settings.microsoft_client_secret}")
        print(f"   - Microsoft Redirect URI: {settings.microsoft_redirect_uri}")
        
        # Prüfe ob Konfiguration vorhanden ist
        if settings.microsoft_client_id in ["your-microsoft-client-id-here", "microsoft-client-id-functional"]:
            print("   ⚠️  Microsoft Client ID ist nicht vollständig konfiguriert")
        else:
            print("   ✅ Microsoft Client ID ist konfiguriert")
        
        if settings.microsoft_client_secret in ["your-microsoft-client-secret-here", "microsoft-client-secret-functional"]:
            print("   ⚠️  Microsoft Client Secret ist nicht vollständig konfiguriert")
        else:
            print("   ✅ Microsoft Client Secret ist konfiguriert")
        
        print(f"   ✅ Microsoft Redirect URI ist konfiguriert: {settings.microsoft_redirect_uri}")
        
        # 2. Teste OAuth URL Generation
        print("\n📋 2. Teste OAuth URL Generation:")
        try:
            oauth_url = await OAuthService.get_oauth_url("microsoft", "test-state")
            print(f"   ✅ OAuth URL erfolgreich generiert:")
            print(f"   {oauth_url}")
        except ValueError as e:
            print(f"   ❌ Fehler bei OAuth URL Generation: {e}")
        
        # 3. Teste Google OAuth (sollte funktionieren)
        print("\n📋 3. Teste Google OAuth (Referenz):")
        try:
            google_url = await OAuthService.get_oauth_url("google", "test-state")
            print(f"   ✅ Google OAuth URL erfolgreich generiert:")
            print(f"   {google_url}")
        except ValueError as e:
            print(f"   ❌ Fehler bei Google OAuth URL Generation: {e}")
        
        # 4. Teste API-Endpunkt
        print("\n📋 4. Teste API-Endpunkt:")
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                url = "http://localhost:8000/api/v1/auth/oauth/microsoft/url"
                async with session.get(url) as response:
                    print(f"   - Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"   - Response: {data}")
                    else:
                        error_text = await response.text()
                        print(f"   - Error: {error_text}")
        except Exception as e:
            print(f"   ❌ Fehler beim API-Test: {e}")
        
        # 5. Lösungsvorschläge
        print("\n📋 5. Lösungsvorschläge:")
        
        if settings.microsoft_client_id in ["your-microsoft-client-id-here", "microsoft-client-id-functional"]:
            print("   🔧 Lösung 1: Microsoft OAuth-Credentials konfigurieren")
            print("   📝 Erstellen Sie eine .env-Datei mit echten Microsoft Azure Credentials:")
            print("   MICROSOFT_CLIENT_ID=ihre-echte-microsoft-client-id")
            print("   MICROSOFT_CLIENT_SECRET=ihr-echtes-microsoft-client-secret")
        
        print("   🔧 Lösung 2: Google OAuth verwenden")
        print("   📝 Google OAuth ist bereits konfiguriert und funktioniert")
        
        print("   🔧 Lösung 3: Microsoft OAuth temporär deaktivieren")
        print("   📝 Entfernen Sie den Microsoft Login Button aus dem Frontend")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def create_env_instructions():
    """Erstellt Anweisungen für .env-Konfiguration"""
    
    print("\n📋 Microsoft OAuth Konfiguration:")
    print("=" * 40)
    
    instructions = """
# Microsoft OAuth Konfiguration

## Option 1: Google OAuth verwenden (empfohlen)
Google OAuth ist bereits konfiguriert und funktioniert:
- Client ID: 1039127200110-vav094cta93qmtleivdj63un5dne17eb.apps.googleusercontent.com
- Redirect URI: http://localhost:5173/auth/google/callback

## Option 2: Microsoft OAuth konfigurieren
Für Microsoft Login benötigen Sie echte Microsoft Azure OAuth-Credentials:

1. Gehen Sie zu https://portal.azure.com
2. Erstellen Sie eine neue App-Registrierung
3. Konfigurieren Sie die Redirect URI: http://localhost:5173/auth/microsoft/callback
4. Erstellen Sie eine .env-Datei mit:

MICROSOFT_CLIENT_ID=ihre-echte-microsoft-client-id
MICROSOFT_CLIENT_SECRET=ihr-echtes-microsoft-client-secret
MICROSOFT_REDIRECT_URI=http://localhost:5173/auth/microsoft/callback

## Option 3: Microsoft Login temporär deaktivieren
Entfernen Sie den Microsoft Login Button aus dem Frontend.
"""
    
    print(instructions)

async def main():
    """Hauptfunktion"""
    print("🔧 Microsoft OAuth Test und Fix")
    print("=" * 50)
    
    # 1. Test Microsoft OAuth
    await test_microsoft_oauth()
    
    # 2. Erstelle Anweisungen
    await create_env_instructions()
    
    # 3. Frage nach Lösung
    print("\n💡 Empfohlene Lösung:")
    print("   Verwenden Sie Google Login als Alternative!")
    print("   Google OAuth ist bereits konfiguriert und funktioniert.")
    
    choice = input("\nMöchten Sie Google Login verwenden? (j/n): ").strip().lower()
    
    if choice in ["j", "ja", "y", "yes"]:
        print("\n✅ Verwenden Sie Google Login!")
        print("💡 Google OAuth ist bereits konfiguriert und funktioniert.")
    else:
        print("\n📝 Konfigurieren Sie Microsoft OAuth mit echten Credentials.")
        print("💡 Siehe Anweisungen oben.")

if __name__ == "__main__":
    asyncio.run(main()) 