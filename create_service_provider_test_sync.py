#!/usr/bin/env python3
"""
Skript zum Erstellen eines Dienstleister-Test-Accounts für BuildWise (synchrone Version)
Verwendung: python create_service_provider_test_sync.py
"""

import sys
import os
from pathlib import Path

# Füge das app-Verzeichnis zum Python-Pfad hinzu
sys.path.append(str(Path(__file__).parent))

from app.core.database import engine
from app.services.user_service import create_user, get_user_by_email
from app.schemas.user import UserCreate
from app.models.user import UserType
from sqlalchemy.orm import sessionmaker

def create_service_provider_test_user():
    """Erstellt einen Dienstleister-Test-Account"""
    
    # Dienstleister-Test-Account-Daten
    service_provider_data = {
        "email": "test-dienstleister@buildwise.de",
        "password": "Test1234!Secure",  # Sicheres Passwort
        "first_name": "Test",
        "last_name": "Dienstleister",
        "phone": "+49 123 456789",
        "user_type": UserType.SERVICE_PROVIDER,  # Wichtig: SERVICE_PROVIDER Typ
        "company_name": "Test Dienstleister GmbH",
        "company_address": "Dienstleisterstraße 456, 12345 Teststadt",
        "company_phone": "+49 123 456789",
        "company_website": "https://test-dienstleister.de",
        "business_license": "DE987654321",
        "bio": "Test-Dienstleister für BuildWise",
        "region": "Deutschland",
        "languages": "de,en",
        "language_preference": "de"
    }
    
    try:
        # Synchrone Session erstellen
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        try:
            # Prüfen, ob Dienstleister bereits existiert
            existing_user = get_user_by_email(session, service_provider_data["email"])
            
            if existing_user:
                print(f"❌ Dienstleister-Account mit E-Mail {service_provider_data['email']} existiert bereits!")
                print(f"   Benutzer-ID: {existing_user.id}")
                print(f"   Erstellt am: {existing_user.created_at}")
                print(f"   Benutzertyp: {existing_user.user_type}")
                return False
            
            # Dienstleister-Account erstellen
            user_create = UserCreate(**service_provider_data)
            service_provider_user = create_user(session, user_create)
            
            # User-Daten für Ausgabe sammeln
            user_id = service_provider_user.id
            user_email = service_provider_user.email
            user_first_name = service_provider_user.first_name
            user_last_name = service_provider_user.last_name
            user_type = service_provider_user.user_type.value
            user_company = service_provider_user.company_name
            user_created = service_provider_user.created_at
            
            # Änderungen committen
            session.commit()
            
            print("✅ Dienstleister-Test-Account erfolgreich erstellt!")
            print(f"   Benutzer-ID: {user_id}")
            print(f"   Name: {user_first_name} {user_last_name}")
            print(f"   E-Mail: {user_email}")
            print(f"   Unternehmen: {user_company}")
            print(f"   Benutzertyp: {user_type}")
            print(f"   Erstellt am: {user_created}")
            print()
            print("🔑 Login-Daten:")
            print(f"   E-Mail: {service_provider_data['email']}")
            print(f"   Passwort: {service_provider_data['password']}")
            print("   ⚠️  Frontend verwendet: Test1234!Secure")
            print()
            print("🚀 Sie können sich jetzt mit dem Dienstleister-Test-Account anmelden!")
            return True
            
        finally:
            session.close()
                
    except Exception as e:
        print(f"❌ Fehler beim Erstellen des Dienstleister-Accounts: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 Dienstleister-Test-Account Erstellung (synchrone Version)")
    print("=" * 60)
    
    try:
        result = create_service_provider_test_user()
        if result:
            print("✅ Dienstleister-Test-Account-Erstellung erfolgreich!")
        else:
            print("❌ Dienstleister-Test-Account-Erstellung fehlgeschlagen!")
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
        print("❌ Dienstleister-Test-Account-Erstellung fehlgeschlagen!") 