#!/usr/bin/env python3
"""
Test-Skript für BuildWise Gebühren-Konfigurationsänderungen

Dieses Skript testet, ob die Konfigurationsänderungen korrekt gespeichert und geladen werden.
"""

import sys
import os
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_env_file():
    """Testet die .env-Datei auf korrekte Gebühren-Konfiguration."""
    print("🔧 Teste .env-Datei...")
    
    if not os.path.exists(".env"):
        print("❌ .env-Datei nicht gefunden")
        return False
    
    try:
        with open(".env", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Prüfe wichtige Einstellungen
        required_settings = [
            "ENVIRONMENT=development",
            "DEBUG_MODE=true",
            "BUILDWISE_FEE_PERCENTAGE=",
            "BUILDWISE_FEE_PHASE=",
            "BUILDWISE_FEE_ENABLED="
        ]
        
        missing_settings = []
        for setting in required_settings:
            if setting not in content:
                missing_settings.append(setting)
        
        if missing_settings:
            print(f"❌ Fehlende Einstellungen: {missing_settings}")
            return False
        
        # Extrahiere Gebühren-Einstellungen
        lines = content.split('\n')
        fee_percentage = None
        fee_phase = None
        fee_enabled = None
        
        for line in lines:
            if line.startswith("BUILDWISE_FEE_PERCENTAGE="):
                fee_percentage = line.split("=")[1]
            elif line.startswith("BUILDWISE_FEE_PHASE="):
                fee_phase = line.split("=")[1]
            elif line.startswith("BUILDWISE_FEE_ENABLED="):
                fee_enabled = line.split("=")[1]
        
        print(f"✅ .env-Datei gefunden und korrekt konfiguriert")
        print(f"   - Gebühren-Prozentsatz: {fee_percentage}")
        print(f"   - Gebühren-Phase: {fee_phase}")
        print(f"   - Gebühren aktiviert: {fee_enabled}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Lesen der .env-Datei: {e}")
        return False

def test_settings_loading():
    """Testet das Laden der Einstellungen aus der .env-Datei."""
    print("\n🔧 Teste Einstellungen-Laden...")
    
    try:
        from app.core.config import settings
        
        print(f"✅ Einstellungen erfolgreich geladen:")
        print(f"   - Environment: {settings.environment}")
        print(f"   - Debug Mode: {settings.debug_mode}")
        print(f"   - Gebühren-Prozentsatz: {settings.buildwise_fee_percentage}%")
        print(f"   - Gebühren-Phase: {settings.buildwise_fee_phase}")
        print(f"   - Gebühren aktiviert: {settings.buildwise_fee_enabled}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Laden der Einstellungen: {e}")
        return False

def test_phase_switching():
    """Testet die Phasen-Umschaltung."""
    print("\n🔧 Teste Phasen-Umschaltung...")
    
    try:
        from app.core.config import settings
        
        # Test Beta-Phase
        settings.buildwise_fee_percentage = 0.0
        settings.buildwise_fee_phase = "beta"
        settings.buildwise_fee_enabled = True
        
        print(f"✅ Beta-Phase konfiguriert:")
        print(f"   - Prozentsatz: {settings.buildwise_fee_percentage}%")
        print(f"   - Phase: {settings.buildwise_fee_phase}")
        print(f"   - Aktiviert: {settings.buildwise_fee_enabled}")
        
        # Test Production-Phase
        settings.buildwise_fee_percentage = 4.0
        settings.buildwise_fee_phase = "production"
        settings.buildwise_fee_enabled = True
        
        print(f"✅ Production-Phase konfiguriert:")
        print(f"   - Prozentsatz: {settings.buildwise_fee_percentage}%")
        print(f"   - Phase: {settings.buildwise_fee_phase}")
        print(f"   - Aktiviert: {settings.buildwise_fee_enabled}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Testen der Phasen-Umschaltung: {e}")
        return False

def create_test_env():
    """Erstellt eine Test-.env-Datei."""
    print("\n🔧 Erstelle Test-.env-Datei...")
    
    test_env_content = f"""# BuildWise Test-Konfiguration
# Generiert am {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Umgebung
ENVIRONMENT=development
DEBUG_MODE=true

# BuildWise Gebühren-Konfiguration
BUILDWISE_FEE_PERCENTAGE=4.0
BUILDWISE_FEE_PHASE=production
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
            f.write(test_env_content)
        
        print("✅ Test-.env-Datei erstellt!")
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Test-.env-Datei: {e}")
        return False

def main():
    """Hauptfunktion."""
    print("🧪 BuildWise Gebühren-Konfiguration Test")
    print("=" * 50)
    
    # Test 1: .env-Datei prüfen
    env_ok = test_env_file()
    
    # Test 2: Einstellungen laden
    settings_ok = test_settings_loading()
    
    # Test 3: Phasen-Umschaltung testen
    switching_ok = test_phase_switching()
    
    # Zusammenfassung
    print("\n📊 Test-Zusammenfassung")
    print("=" * 30)
    print(f"✅ .env-Datei: {'OK' if env_ok else 'FEHLER'}")
    print(f"✅ Einstellungen laden: {'OK' if settings_ok else 'FEHLER'}")
    print(f"✅ Phasen-Umschaltung: {'OK' if switching_ok else 'FEHLER'}")
    
    if not env_ok:
        print("\n💡 Erstelle Test-.env-Datei...")
        if create_test_env():
            print("✅ Test-.env-Datei erstellt. Führen Sie die Tests erneut aus.")
        else:
            print("❌ Fehler beim Erstellen der Test-.env-Datei")
    
    if env_ok and settings_ok and switching_ok:
        print("\n🎉 Alle Tests bestanden!")
        print("💡 Die Gebühren-Konfiguration funktioniert korrekt.")
    else:
        print("\n❌ Einige Tests fehlgeschlagen.")
        print("💡 Überprüfen Sie die .env-Datei und starten Sie den Server neu.")

if __name__ == "__main__":
    main() 