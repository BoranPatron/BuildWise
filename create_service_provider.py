#!/usr/bin/env python3
"""
Skript zum Erstellen eines Dienstleister-Benutzers für BuildWise
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal
from app.models.user import User, UserType, UserStatus
from app.services.security_service import SecurityService
from sqlalchemy import select

async def create_service_provider():
    """Erstellt einen Dienstleister-Benutzer"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Prüfe ob Dienstleister bereits existiert
            stmt = select(User).where(User.email == "dienstleister@buildwise.de")
            result = await db.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"✅ Dienstleister existiert bereits: {existing_user.email}")
                return existing_user
            
            # Dienstleister erstellen
            hashed_password = SecurityService.hash_password("Dienstleister123!")
            
            service_provider = User(
                email="dienstleister@buildwise.de",
                hashed_password=hashed_password,
                first_name="Max",
                last_name="Mustermann",
                phone="+41 44 123 45 67",
                user_type=UserType.SERVICE_PROVIDER,
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
            print(f"   - Name: {service_provider.first_name} {service_provider.last_name}")
            print(f"   - Firma: {service_provider.company_name}")
            print(f"   - Adresse: {service_provider.company_address}")
            print(f"   - Passwort: Dienstleister123!")
            
            return service_provider
            
        except Exception as e:
            print(f"❌ Fehler beim Erstellen des Dienstleisters: {e}")
            return None

async def main():
    """Hauptfunktion"""
    print("🚀 Erstelle Dienstleister-Benutzer für BuildWise...")
    
    service_provider = await create_service_provider()
    
    if service_provider:
        print("\n🎉 Dienstleister erstellt! Login-Daten:")
        print(f"   E-Mail: {service_provider.email}")
        print(f"   Passwort: Dienstleister123!")
    else:
        print("\n❌ Fehler beim Erstellen des Dienstleisters!")

if __name__ == "__main__":
    asyncio.run(main()) 