#!/usr/bin/env python3
"""
Skript zum Erstellen des korrekten Dienstleister-Users für das Frontend
"""

import asyncio
import sys
import os

# Füge das aktuelle Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.user import User, UserType, UserStatus, UserRole
from app.services.security_service import SecurityService
from sqlalchemy import select

async def create_test_dienstleister():
    """Erstellt den korrekten Dienstleister-User"""
    try:
        async for db in get_db():
            # Prüfe ob User bereits existiert
            stmt = select(User).where(User.email == 'test-dienstleister@buildwise.de')
            result = await db.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"✅ Dienstleister existiert bereits: {existing_user.email}")
                print(f"   User ID: {existing_user.id}")
                print(f"   User Role: {existing_user.user_role}")
                print(f"   Is Active: {existing_user.is_active}")
                return existing_user
            
            # User erstellen
            hashed_password = SecurityService.hash_password("Dienstleister123!")
            
            service_provider = User(
                email="test-dienstleister@buildwise.de",
                hashed_password=hashed_password,
                first_name="Max",
                last_name="Mustermann",
                phone="+41 44 123 45 67",
                user_type=UserType.SERVICE_PROVIDER,
                user_role=UserRole.DIENSTLEISTER,
                status=UserStatus.ACTIVE,
                is_active=True,
                is_verified=True,
                # DSGVO-Einwilligungen
                data_processing_consent=True,
                marketing_consent=True,
                privacy_policy_accepted=True,
                terms_accepted=True,
                # Dienstleister-spezifische Felder
                company_name="Mustermann Bau GmbH",
                company_address="Dienstleisterstraße 1, 8001 Zürich",
                company_phone="+41 44 123 45 67",
                company_website="https://www.mustermann-bau.ch"
            )
            
            db.add(service_provider)
            await db.commit()
            await db.refresh(service_provider)
            
            print(f"✅ Dienstleister erstellt: {service_provider.email}")
            print(f"📋 Details:")
            print(f"   - User ID: {service_provider.id}")
            print(f"   - User Role: {service_provider.user_role}")
            print(f"   - Is Active: {service_provider.is_active}")
            print(f"   - Passwort: Dienstleister123!")
            
            return service_provider
            
    except Exception as e:
        print(f"❌ Fehler beim Erstellen des Dienstleisters: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Erstelle Dienstleister-User für Frontend...")
    print("📧 E-Mail: test-dienstleister@buildwise.de")
    print("🔑 Passwort: Dienstleister123!")
    
    user = asyncio.run(create_test_dienstleister())
    
    if user:
        print("\n🎉 Dienstleister erstellt/gefunden!")
        print("💡 Login sollte jetzt im Frontend funktionieren!")
    else:
        print("\n❌ Fehler beim Erstellen des Dienstleisters!") 