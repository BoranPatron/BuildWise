#!/usr/bin/env python3
"""
Skript zum Erstellen eines Dienstleister-Test-Accounts für BuildWise
Verwendung: python create_service_provider_test.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.user import User, UserType, UserStatus
from app.core.security import get_password_hash
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def create_service_provider_test():
    """Erstellt einen Test-Dienstleister-Account für die Frontend-Tests"""
    
    async for db in get_db():
        try:
            # Prüfe ob der Test-Account bereits existiert
            stmt = select(User).where(User.email == "test-dienstleister@buildwise.de")
            result = await db.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print("✅ Test-Dienstleister-Account existiert bereits:")
                print(f"   E-Mail: {existing_user.email}")
                print(f"   Name: {existing_user.first_name} {existing_user.last_name}")
                print(f"   Typ: {existing_user.user_type}")
                print(f"   Status: {existing_user.status}")
                print(f"   Aktiv: {existing_user.is_active}")
                print(f"   DSGVO-Einwilligung: {existing_user.data_processing_consent}")
                
                # Aktualisiere DSGVO-Einwilligungen falls nötig
                if not existing_user.data_processing_consent:
                    existing_user.data_processing_consent = True
                    existing_user.privacy_policy_accepted = True
                    existing_user.terms_accepted = True
                    await db.commit()
                    print("✅ DSGVO-Einwilligungen wurden aktualisiert")
                
                return
            
            # Erstelle neuen Test-Dienstleister
            hashed_password = get_password_hash("Test1234!Secure")
            
            new_user = User(
                email="test-dienstleister@buildwise.de",
                hashed_password=hashed_password,
                first_name="Test",
                last_name="Dienstleister",
                user_type=UserType.SERVICE_PROVIDER,
                status=UserStatus.ACTIVE,
                is_active=True,
                is_verified=True,
                email_verified=True,
                # DSGVO-Einwilligungen
                data_processing_consent=True,
                privacy_policy_accepted=True,
                terms_accepted=True,
                # Firmendaten
                company_name="Test Bau GmbH",
                company_address="Musterstraße 123, 12345 Musterstadt",
                company_phone="+49 123 456789",
                company_website="https://test-bau.de",
                region="Deutschland",
                # Profil
                bio="Test-Dienstleister für BuildWise Frontend-Tests",
                languages="Deutsch, Englisch"
            )
            
            db.add(new_user)
            await db.commit()
            
            print("✅ Test-Dienstleister-Account erfolgreich erstellt:")
            print(f"   E-Mail: {new_user.email}")
            print(f"   Passwort: Test1234!Secure")
            print(f"   Name: {new_user.first_name} {new_user.last_name}")
            print(f"   Typ: {new_user.user_type}")
            print(f"   Status: {new_user.status}")
            print(f"   Aktiv: {new_user.is_active}")
            print(f"   DSGVO-Einwilligung: {new_user.data_processing_consent}")
            print(f"   Firma: {new_user.company_name}")
            
        except Exception as e:
            print(f"❌ Fehler beim Erstellen des Test-Dienstleisters: {e}")
            await db.rollback()
            raise
        finally:
            await db.close()

if __name__ == "__main__":
    asyncio.run(create_service_provider_test()) 