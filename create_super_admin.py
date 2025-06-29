#!/usr/bin/env python3
"""
Skript zum Erstellen eines Super-Admin-Accounts für BuildWise
Verwendung: python create_super_admin.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Füge das app-Verzeichnis zum Python-Pfad hinzu
sys.path.append(str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal
from app.services.user_service import create_user, get_user_by_email
from app.schemas.user import UserCreate
from app.models.user import UserType

async def create_super_admin():
    """Erstellt einen Super-Admin-Account mit allen Berechtigungen"""
    
    # Super-Admin-Account-Daten
    admin_data = {
        "email": "admin@buildwise.de",
        "password": "admin123",  # In Produktion sollte dies sicherer sein
        "first_name": "Super",
        "last_name": "Admin",
        "phone": "+49 123 456789",
        "user_type": UserType.SERVICE_PROVIDER,  # Höchste Berechtigungen
        "company_name": "BuildWise GmbH",
        "company_address": "Musterstraße 123, 12345 Musterstadt",
        "company_phone": "+49 123 456789",
        "company_website": "https://buildwise.de",
        "business_license": "DE123456789",
        "bio": "Super-Administrator für BuildWise mit allen Berechtigungen",
        "region": "Deutschland",
        "languages": "de,en",
        "language_preference": "de"
    }
    
    try:
        # Verwende AsyncSessionLocal für die Session-Verwaltung
        async with AsyncSessionLocal() as session:
            # Prüfen, ob Admin bereits existiert
            existing_user = await get_user_by_email(session, admin_data["email"])
            
            if existing_user:
                print(f"❌ Super-Admin mit E-Mail {admin_data['email']} existiert bereits!")
                print(f"   Benutzer-ID: {existing_user.id}")
                print(f"   Erstellt am: {existing_user.created_at}")
                print(f"   Typ: {existing_user.user_type.value}")
                return False
            
            # Super-Admin-Account erstellen
            user_create = UserCreate(**admin_data)
            admin_user = await create_user(session, user_create)
            
            # Änderungen committen
            await session.commit()
            
            print("✅ Super-Admin-Account erfolgreich erstellt!")
            print(f"   Benutzer-ID: {admin_user.id}")
            print(f"   E-Mail: {admin_user.email}")
            print(f"   Name: {admin_user.first_name} {admin_user.last_name}")
            print(f"   Typ: {admin_user.user_type.value}")
            print(f"   Firma: {admin_user.company_name}")
            print(f"   Erstellt am: {admin_user.created_at}")
            print()
            print("🔑 Login-Daten:")
            print(f"   E-Mail: {admin_data['email']}")
            print(f"   Passwort: {admin_data['password']}")
            print()
            print("⚠️  WICHTIG: Ändern Sie das Passwort nach dem ersten Login!")
            print("🚀 Dieser Super-Admin hat alle Berechtigungen für API-Tests!")
            return True
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen des Super-Admin-Accounts: {e}")
        return False

async def main():
    """Hauptfunktion"""
    print("🚀 BuildWise Super-Admin-Account Erstellung")
    print("=" * 50)
    
    success = await create_super_admin()
    
    if success:
        print("✅ Super-Admin-Account-Erstellung abgeschlossen!")
        print()
        print("📝 Nächste Schritte:")
        print("1. Starten Sie das Backend: python -m uvicorn app.main:app --reload")
        print("2. Starten Sie das Frontend: npm run dev")
        print("3. Melden Sie sich mit den Super-Admin-Daten an")
        print("4. Testen Sie alle API-Funktionen über das Frontend")
    else:
        print("❌ Super-Admin-Account-Erstellung fehlgeschlagen!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 