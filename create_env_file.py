#!/usr/bin/env python3
"""
Erstellt eine .env-Datei mit den korrekten Einstellungen für den Entwicklungsmodus.
"""

import os
from datetime import datetime

def create_env_file():
    """Erstellt eine .env-Datei mit den korrekten Einstellungen."""
    
    env_content = f"""# BuildWise Entwicklungsmodus-Konfiguration
# Generiert am {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Umgebung
ENVIRONMENT=development
DEBUG_MODE=true

# BuildWise Gebühren-Konfiguration
BUILDWISE_FEE_PERCENTAGE=0.0
BUILDWISE_FEE_PHASE=beta
BUILDWISE_FEE_ENABLED=true

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

# Microsoft OAuth (optional)
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
MICROSOFT_REDIRECT_URI=http://localhost:5173/auth/microsoft/callback

# Sicherheit
BCRYPT_ROUNDS=12
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION_MINUTES=30

# DSGVO
DATA_RETENTION_DAYS=730
CONSENT_REQUIRED=true
"""
    
    try:
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_content)
        
        print("✅ .env-Datei erfolgreich erstellt!")
        print("🔧 Entwicklungsmodus ist jetzt aktiviert")
        print("🐛 Debug-Funktionen sind verfügbar")
        
        return True
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der .env-Datei: {e}")
        return False

def check_env_file():
    """Prüft ob die .env-Datei existiert und korrekt konfiguriert ist."""
    
    if not os.path.exists(".env"):
        print("⚠️  .env-Datei nicht gefunden")
        return False
    
    try:
        with open(".env", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Prüfe wichtige Einstellungen
        if "ENVIRONMENT=development" in content and "DEBUG_MODE=true" in content:
            print("✅ .env-Datei ist korrekt konfiguriert")
            print("🔧 Entwicklungsmodus ist aktiviert")
            return True
        else:
            print("⚠️  .env-Datei ist nicht korrekt konfiguriert")
            return False
            
    except Exception as e:
        print(f"❌ Fehler beim Lesen der .env-Datei: {e}")
        return False

def main():
    """Hauptfunktion."""
    print("🔧 BuildWise .env-Datei Setup")
    print("=" * 40)
    
    # Prüfe ob .env-Datei bereits existiert
    if check_env_file():
        print("\n💡 .env-Datei existiert bereits und ist korrekt konfiguriert")
        print("🐛 Debug-Funktionen sollten jetzt funktionieren")
        return
    
    # Erstelle neue .env-Datei
    print("\n📝 Erstelle neue .env-Datei...")
    if create_env_file():
        print("\n🎉 Setup abgeschlossen!")
        print("🐛 Debug-Funktionen sind jetzt verfügbar")
        print("\n💡 Nächste Schritte:")
        print("   1. Starten Sie den Backend-Server neu")
        print("   2. Testen Sie den Debug-Button")
    else:
        print("\n❌ Setup fehlgeschlagen")

if __name__ == "__main__":
    main() 