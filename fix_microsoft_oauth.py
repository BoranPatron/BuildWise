#!/usr/bin/env python3
"""
Skript zur Korrektur der Microsoft OAuth-Konfiguration
"""

import os

def create_correct_env():
    """Erstellt eine korrekte .env-Datei"""
    
    env_content = """# Microsoft OAuth Configuration
MICROSOFT_CLIENT_ID=c5247a29-0cb4-4cdf-9f4c-a091a3a42383
MICROSOFT_CLIENT_SECRET=IHRE_CLIENT_SECRET_VALUE_HIER_EINSETZEN
MICROSOFT_REDIRECT_URI=http://localhost:5173/auth/microsoft/callback

# Bestehende Google OAuth
GOOGLE_CLIENT_ID=1039127200110-vav094cta93qmtleivdj63un5dne17eb.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_REDIRECT_URI=http://localhost:5173/auth/google/callback

# JWT Configuration
SECRET_KEY=your-secret-key-here-change-in-production
JWT_SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite:///./buildwise.db

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Security
BCRYPT_ROUNDS=12
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION_MINUTES=30

# DSGVO
DATA_RETENTION_DAYS=730
CONSENT_REQUIRED=true
"""
    
    # .env-Datei erstellen
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ .env-Datei erstellt!")
    print("⚠️  WICHTIG: Ersetzen Sie 'IHRE_CLIENT_SECRET_VALUE_HIER_EINSETZEN'")
    print("   mit dem korrekten Client Secret Value aus dem Azure Portal!")
    print("\n📝 Anleitung:")
    print("   1. Azure Portal öffnen: https://portal.azure.com/")
    print("   2. App registrations → BuildWise → Certificates & secrets")
    print("   3. Kopieren Sie den 'Value' (nicht die ID!)")
    print("   4. Ersetzen Sie 'IHRE_CLIENT_SECRET_VALUE_HIER_EINSETZEN' in .env")
    print("   5. Backend neu starten")

def check_azure_portal_instructions():
    """Zeigt detaillierte Anweisungen für Azure Portal"""
    
    print("\n🔍 Detaillierte Azure Portal Anweisungen:")
    print("=" * 50)
    print("1. Öffnen Sie https://portal.azure.com/")
    print("2. Klicken Sie auf 'App registrations'")
    print("3. Klicken Sie auf Ihre 'BuildWise'-App")
    print("4. Im linken Menü: 'Certificates & secrets'")
    print("5. Unter 'Client secrets' sehen Sie eine Tabelle:")
    print("   - Name: BuildWise OAuth Secret")
    print("   - Expires: Never")
    print("   - Value: [Kopieren Sie diesen Wert!]")
    print("6. Klicken Sie auf das Kopier-Symbol neben 'Value'")
    print("7. Fügen Sie den Wert in die .env-Datei ein")
    print("\n⚠️  WICHTIG: Verwenden Sie den 'Value', nicht die 'ID'!")

if __name__ == "__main__":
    create_correct_env()
    check_azure_portal_instructions() 