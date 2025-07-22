#!/usr/bin/env python3
"""
Skript zum Erstellen eines Testbenutzers für BuildWise
"""

import asyncio
import sys
import os
from pathlib import Path

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal
from app.services.user_service import create_user
from app.schemas.user import UserCreate
from app.models.user import UserType, AuthProvider
from passlib.context import CryptContext

# Passwort-Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_test_user():
    """Erstellt einen Testbenutzer mit den Login-Daten admin@buildwise.de"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Testbenutzer-Daten
            test_user_data = UserCreate(
                email="admin@buildwise.de",
                password="Admin123!",  # Stärkeres Passwort
                first_name="Admin",
                last_name="BuildWise",
                user_type=UserType.PRIVATE,
                data_processing_consent=True,
                privacy_policy_accepted=True,
                terms_accepted=True
            )
            
            # Benutzer erstellen
            user = await create_user(db, test_user_data)
            
            print(f"✅ Testbenutzer erfolgreich erstellt!")
            print(f"📧 E-Mail: {user.email}")
            print(f"👤 Name: {user.first_name} {user.last_name}")
            print(f"🔑 Passwort: Admin123!")
            print(f"🔐 Auth Provider: {user.auth_provider}")
            print(f"✅ DSGVO-Einwilligungen: {user.data_processing_consent}")
            
            return user
            
        except Exception as e:
            print(f"❌ Fehler beim Erstellen des Testbenutzers: {e}")
            return None

async def main():
    """Hauptfunktion"""
    print("🚀 Erstelle Testbenutzer für BuildWise...")
    
    user = await create_test_user()
    
    if user:
        print("\n🎉 Testbenutzer erstellt! Du kannst dich jetzt einloggen mit:")
        print("   E-Mail: admin@buildwise.de")
        print("   Passwort: Admin123!")
    else:
        print("\n❌ Fehler beim Erstellen des Testbenutzers!")

if __name__ == "__main__":
    asyncio.run(main()) 