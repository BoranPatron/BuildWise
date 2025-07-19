#!/usr/bin/env python3
"""
Setup-Script für BuildWise Datenbank
Erstellt alle Tabellen und fügt Test-Accounts hinzu
"""

import asyncio
import sys
import os
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, get_db
from app.models.base import Base
from app.models.user import User, UserType, SubscriptionPlan, UserStatus
from app.core.security import get_password_hash


async def setup_database():
    """Erstellt alle Tabellen und fügt Test-Accounts hinzu"""
    
    print("🔧 Erstelle Datenbank-Tabellen...")
    
    # Erstelle alle Tabellen
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Tabellen erstellt")
    
    # Erstelle Test-Accounts
    async for db in get_db():
        try:
            print("🔧 Erstelle Test-Accounts...")
            
            # 1. Admin Account
            admin_data = {
                "email": "admin@buildwise.de",
                "hashed_password": get_password_hash("Admin123!"),
                "first_name": "System",
                "last_name": "Administrator",
                "phone": "+49 123 456789",
                "user_type": UserType.PROFESSIONAL,
                "subscription_plan": SubscriptionPlan.PRO,
                "subscription_start_date": date.today(),
                "subscription_active": True,
                "status": UserStatus.ACTIVE,
                "data_processing_consent": True,
                "marketing_consent": True,
                "privacy_policy_accepted": True,
                "terms_accepted": True,
                "email_verified": True,
                "email_verified_at": datetime.utcnow(),
                "is_active": True,
                "is_verified": True,
                "roles": ["admin"],
                "permissions": {"*": True},
                "language_preference": "de",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                # Passwort-Reset-Felder (leer für Admin)
                "password_reset_token": None,
                "password_reset_sent_at": None,
                "password_reset_expires_at": None
            }
            
            # Prüfe ob Admin bereits existiert
            result = await db.execute(select(User).where(User.email == admin_data["email"]))
            existing_admin = result.scalar_one_or_none()
            
            if existing_admin:
                print(f"✅ Admin-Account bereits vorhanden: {admin_data['email']}")
            else:
                admin = User(**admin_data)
                db.add(admin)
                await db.commit()
                await db.refresh(admin)
                print(f"✅ Admin-Account erstellt: {admin_data['email']} (ID: {admin.id})")
            
            # 2. Dienstleister Account
            service_provider_data = {
                "email": "test-dienstleister@buildwise.de",
                "hashed_password": get_password_hash("test1234"),
                "first_name": "Max",
                "last_name": "Mustermann",
                "phone": "+49 987 654321",
                "user_type": UserType.SERVICE_PROVIDER,
                "subscription_plan": SubscriptionPlan.BASIS,
                "subscription_start_date": date.today(),
                "subscription_active": True,
                "status": UserStatus.ACTIVE,
                "data_processing_consent": True,
                "marketing_consent": True,
                "privacy_policy_accepted": True,
                "terms_accepted": True,
                "email_verified": True,
                "email_verified_at": datetime.utcnow(),
                "is_active": True,
                "is_verified": True,
                "company_name": "Mustermann Bau GmbH",
                "company_address": "Musterstraße 123, 12345 Musterstadt",
                "company_phone": "+49 987 654321",
                "company_website": "https://www.mustermann-bau.de",
                "business_license": "Gewerbeschein 12345",
                "tax_id": "123/456/78901",
                "vat_id": "DE123456789",
                "bio": "Erfahrener Bauunternehmer mit 15 Jahren Erfahrung",
                "region": "Bayern",
                "languages": "Deutsch, Englisch",
                "roles": ["service_provider"],
                "permissions": {
                    "view_trades": True,
                    "create_quotes": True,
                    "view_projects": True,
                    "view_milestones": True,
                    "view_documents": True,
                    "send_messages": True,
                    "view_buildwise_fees": True
                },
                "language_preference": "de",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Prüfe ob Dienstleister bereits existiert
            result = await db.execute(select(User).where(User.email == service_provider_data["email"]))
            existing_sp = result.scalar_one_or_none()
            
            if existing_sp:
                print(f"✅ Dienstleister-Account bereits vorhanden: {service_provider_data['email']}")
            else:
                sp = User(**service_provider_data)
                db.add(sp)
                await db.commit()
                await db.refresh(sp)
                print(f"✅ Dienstleister-Account erstellt: {service_provider_data['email']} (ID: {sp.id})")
            
            print("\n🎉 Datenbank-Setup erfolgreich!")
            print("\n📋 Account-Übersicht:")
            print("┌─────────────────────────────────────────────────────────────────┐")
            print("│ Admin: admin@buildwise.de / Admin123!                        │")
            print("│ Dienstleister: test-dienstleister@buildwise.de / test1234    │")
            print("└─────────────────────────────────────────────────────────────────┘")
            
        except Exception as e:
            print(f"❌ Fehler beim Setup: {e}")
            await db.rollback()
        finally:
            await db.close()


if __name__ == "__main__":
    asyncio.run(setup_database()) 