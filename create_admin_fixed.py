#!/usr/bin/env python3
"""
Skript zum Erstellen eines Admin-Accounts für BuildWise
Verwendung: python create_admin_fixed.py
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

async def create_admin_user():
    """Erstellt einen Admin-Account mit Best Practices"""
    
    # Admin-Account-Daten (nach Best Practices)
    admin_data = {
        "email": "admin@buildwise.de",
        "password": "admin123",  # In Produktion sollte dies sicherer sein
        "first_name": "Admin",
        "last_name": "BuildWise",
        "phone": "+49 123 456789",
        "user_type": UserType.PROFESSIONAL,
        "company_name": "BuildWise GmbH",
        "company_address": "Musterstraße 123, 12345 Musterstadt",
        "company_phone": "+49 123 456789",
        "company_website": "https://buildwise.de",
        "business_license": "DE123456789",
        "bio": "System-Administrator für BuildWise",
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
                print(f"❌ Admin-Account mit E-Mail {admin_data['email']} existiert bereits!")
                print(f"   Benutzer-ID: {existing_user.id}")
                print(f"   Erstellt am: {existing_user.created_at}")
                return False
            
            # Admin-Account erstellen
            user_create = UserCreate(**admin_data)
            admin_user = await create_user(session, user_create)
            
            # Änderungen committen
            await session.commit()
            
            print("✅ Admin-Account erfolgreich erstellt!")
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
            return True
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen des Admin-Accounts: {e}")
        return False

async def main():
    """Hauptfunktion"""
    print("🚀 BuildWise Admin-Account Erstellung")
    print("=" * 50)
    
    success = await create_admin_user()
    
    if success:
        print("✅ Admin-Account-Erstellung abgeschlossen!")
        print()
        print("📝 Nächste Schritte:")
        print("1. Starten Sie das Backend: python -m uvicorn app.main:app --reload")
        print("2. Starten Sie das Frontend: npm run dev")
        print("3. Melden Sie sich mit den Admin-Daten an")
        print("4. Ändern Sie das Passwort nach dem ersten Login")
    else:
        print("❌ Admin-Account-Erstellung fehlgeschlagen!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 