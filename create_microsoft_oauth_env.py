#!/usr/bin/env python3
"""
Skript zur Erstellung der .env-Datei mit Microsoft OAuth Credentials
"""

import os

def create_env_file():
    """Erstellt eine .env-Datei mit allen notwendigen Konfigurationen"""
    
    env_content = """# BuildWise - Entwicklungsumgebung
# =============================================================================
# DATENBANK-KONFIGURATION
# =============================================================================
DB_HOST=localhost
DB_PORT=5432
DB_NAME=buildwise
DB_USER=postgres
DB_PASSWORD=your_secure_password

# =============================================================================
# JWT & SICHERHEIT
# =============================================================================
JWT_SECRET_KEY=your_super_secret_jwt_key_here_make_it_long_and_random_at_least_32_characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# =============================================================================
# ANWENDUNGSEINSTELLUNGEN
# =============================================================================
DEBUG=True
ENVIRONMENT=development
API_VERSION=v1
APP_NAME=BuildWise
APP_VERSION=1.0.0
TIMEZONE=Europe/Berlin
LANGUAGE=de

# =============================================================================
# SERVER-KONFIGURATION
# =============================================================================
HOST=0.0.0.0
PORT=8000

# =============================================================================
# CORS & SICHERHEIT
# =============================================================================
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173
ALLOWED_METHODS=GET,POST,PUT,DELETE,OPTIONS
ALLOWED_HEADERS=Content-Type,Authorization,X-Requested-With
ALLOW_CREDENTIALS=true

# =============================================================================
# DATEI-UPLOAD
# =============================================================================
MAX_FILE_SIZE=10485760
ALLOWED_FILE_TYPES=pdf,jpg,jpeg,png,docx,xlsx,zip,rar
UPLOAD_PATH=storage/uploads

# =============================================================================
# GOOGLE OAUTH
# =============================================================================
GOOGLE_CLIENT_ID=1039127200110-vav094cta93qmtleivdj63un5dne17eb.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_REDIRECT_URI=http://localhost:5173/auth/google/callback

# =============================================================================
# MICROSOFT OAUTH
# =============================================================================
MICROSOFT_CLIENT_ID=c5247a29-0cb4-4cdf-9f4c-a091a3a42383
MICROSOFT_CLIENT_SECRET=_Hl8Q~tx77qPXElvSyl.GmnjMXSJBwpDlpyWFaDt
MICROSOFT_REDIRECT_URI=http://localhost:5173/auth/microsoft/callback
"""
    
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ .env-Datei erfolgreich erstellt!")
        print("📋 Microsoft OAuth Credentials konfiguriert:")
        print(f"   - Client ID: c5247a29-0cb4-4cdf-9f4c-a091a3a42383")
        print(f"   - Client Secret: _Hl8Q~tx77qPXElvSyl.GmnjMXSJBwpDlpyWFaDt")
        print(f"   - Redirect URI: http://localhost:5173/auth/microsoft/callback")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der .env-Datei: {e}")
        return False

def test_configuration():
    """Testet die Konfiguration nach dem Erstellen der .env-Datei"""
    
    print("\n🔧 Teste Konfiguration...")
    
    try:
        # Importiere Settings nach dem Erstellen der .env-Datei
        from app.core.config import settings
        
        print("✅ Settings erfolgreich geladen")
        print(f"   - Microsoft Client ID: {settings.microsoft_client_id}")
        print(f"   - Microsoft Client Secret: {'✅ Konfiguriert' if settings.microsoft_client_secret else '❌ Fehlt'}")
        print(f"   - Microsoft Redirect URI: {settings.microsoft_redirect_uri}")
        
        if settings.microsoft_client_id and settings.microsoft_client_secret:
            print("✅ Microsoft OAuth ist vollständig konfiguriert!")
            return True
        else:
            print("❌ Microsoft OAuth ist nicht vollständig konfiguriert")
            return False
            
    except Exception as e:
        print(f"❌ Fehler beim Testen der Konfiguration: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Erstelle .env-Datei mit Microsoft OAuth Credentials...")
    
    # Erstelle .env-Datei
    if create_env_file():
        # Teste Konfiguration
        test_configuration()
        
        print("\n🚀 Nächste Schritte:")
        print("1. Starten Sie den Backend-Server neu:")
        print("   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("2. Testen Sie Microsoft OAuth im Frontend")
        print("3. Überprüfen Sie die Azure App-Registrierung")
    else:
        print("❌ Fehler beim Erstellen der .env-Datei") 