#!/usr/bin/env python3
"""
Debug-Skript für Microsoft OAuth-Konfiguration
"""

import sys
import os
import asyncio
from typing import Optional

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def debug_microsoft_oauth():
    """Debuggt die Microsoft OAuth-Konfiguration"""
    
    print("🔍 Debug Microsoft OAuth-Konfiguration")
    print("=" * 50)
    
    try:
        from app.core.config import settings
        from app.services.oauth_service import OAuthService
        
        print("📋 1. Überprüfe Settings:")
        print(f"   - Microsoft Client ID: {settings.microsoft_client_id}")
        print(f"   - Microsoft Client Secret: {settings.microsoft_client_secret}")
        print(f"   - Microsoft Redirect URI: {settings.microsoft_redirect_uri}")
        
        # Prüfe ob Konfiguration vorhanden ist
        if not settings.microsoft_client_id or settings.microsoft_client_id == "your-microsoft-client-id-here":
            print("   ❌ Microsoft Client ID ist nicht konfiguriert!")
            print("   💡 Hinweis: Setzen Sie die echten Microsoft OAuth-Credentials in der .env-Datei")
        else:
            print("   ✅ Microsoft Client ID ist konfiguriert")
        
        if not settings.microsoft_client_secret or settings.microsoft_client_secret == "your-microsoft-client-secret-here":
            print("   ❌ Microsoft Client Secret ist nicht konfiguriert!")
            print("   💡 Hinweis: Setzen Sie die echten Microsoft OAuth-Credentials in der .env-Datei")
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
        
        # 3. Teste API-Endpunkt
        print("\n📋 3. Teste API-Endpunkt:")
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
        
        # 4. Lösungsvorschläge
        print("\n📋 4. Lösungsvorschläge:")
        
        if not settings.microsoft_client_id or settings.microsoft_client_id == "your-microsoft-client-id-here":
            print("   🔧 Lösung 1: Microsoft OAuth-Credentials konfigurieren")
            print("   📝 Erstellen Sie eine .env-Datei mit:")
            print("   MICROSOFT_CLIENT_ID=ihre-microsoft-client-id")
            print("   MICROSOFT_CLIENT_SECRET=ihr-microsoft-client-secret")
        
        print("   🔧 Lösung 2: Microsoft OAuth temporär deaktivieren")
        print("   📝 Kommentieren Sie die Microsoft OAuth-Prüfung aus")
        
        print("   🔧 Lösung 3: Google OAuth verwenden")
        print("   📝 Verwenden Sie Google Login als Alternative")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Debug: {e}")
        import traceback
        traceback.print_exc()
        return False

async def create_env_template():
    """Erstellt eine .env-Template-Datei"""
    
    print("\n📋 Erstelle .env-Template:")
    print("=" * 30)
    
    env_content = """# BuildWise .env Template
# Kopieren Sie diese Datei zu .env und füllen Sie die Werte aus

# Datenbank
DATABASE_URL=sqlite:///./buildwise.db

# JWT
SECRET_KEY=your-secret-key-here-change-in-production
JWT_SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# Google OAuth
GOOGLE_CLIENT_ID=1039127200110-vav094cta93qmtleivdj63un5dne17eb.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_REDIRECT_URI=http://localhost:5173/auth/google/callback

# Microsoft OAuth (OPTIONAL - für Microsoft Login)
MICROSOFT_CLIENT_ID=your-microsoft-client-id-here
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret-here
MICROSOFT_REDIRECT_URI=http://localhost:5173/auth/microsoft/callback

# BuildWise Gebühren-Konfiguration
BUILDWISE_FEE_PERCENTAGE=0.0
BUILDWISE_FEE_PHASE=beta
BUILDWISE_FEE_ENABLED=true

# Umgebung
ENVIRONMENT=development
DEBUG_MODE=true
"""
    
    with open(".env.template", "w", encoding="utf-8") as f:
        f.write(env_content)
    
    print("✅ .env.template erstellt!")
    print("💡 Kopieren Sie diese Datei zu .env und konfigurieren Sie die Microsoft OAuth-Credentials")

async def disable_microsoft_oauth_temporarily():
    """Deaktiviert Microsoft OAuth temporär"""
    
    print("\n📋 Deaktiviere Microsoft OAuth temporär:")
    print("=" * 40)
    
    try:
        from app.services.oauth_service import OAuthService
        
        # Überschreibe die get_oauth_url Methode temporär
        original_get_oauth_url = OAuthService.get_oauth_url
        
        async def temporary_get_oauth_url(provider: str, state: Optional[str] = None) -> str:
            if provider == "microsoft":
                raise ValueError("Microsoft OAuth ist temporär deaktiviert. Verwenden Sie Google Login.")
            return await original_get_oauth_url(provider, state)
        
        OAuthService.get_oauth_url = temporary_get_oauth_url
        
        print("✅ Microsoft OAuth temporär deaktiviert")
        print("💡 Verwenden Sie Google Login als Alternative")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Deaktivieren: {e}")
        return False

async def main():
    """Hauptfunktion"""
    print("🔧 Microsoft OAuth Debug und Fix")
    print("=" * 50)
    
    # 1. Debug Microsoft OAuth
    await debug_microsoft_oauth()
    
    # 2. Erstelle .env-Template
    await create_env_template()
    
    # 3. Frage nach Lösung
    print("\n💡 Wählen Sie eine Lösung:")
    print("   1. Microsoft OAuth-Credentials konfigurieren")
    print("   2. Microsoft OAuth temporär deaktivieren")
    print("   3. Google OAuth verwenden")
    
    choice = input("\nWelche Lösung möchten Sie? (1/2/3): ").strip()
    
    if choice == "1":
        print("\n📝 Konfigurieren Sie die Microsoft OAuth-Credentials in der .env-Datei")
        print("💡 Verwenden Sie das erstellte .env.template als Vorlage")
    elif choice == "2":
        await disable_microsoft_oauth_temporarily()
    elif choice == "3":
        print("\n✅ Verwenden Sie Google Login als Alternative")
        print("💡 Google OAuth ist bereits konfiguriert und funktioniert")
    else:
        print("\n❌ Ungültige Auswahl")

if __name__ == "__main__":
    asyncio.run(main()) 