#!/usr/bin/env python3
"""
Script zur Erstellung von Admin- und Test-Accounts für BuildWise
Erstellt vollständig konfigurierte Accounts mit allen Rechten und DSGVO-Einwilligungen
"""

import asyncio
import sys
import os
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.user import User, UserType, SubscriptionPlan, UserStatus
from app.core.security import get_password_hash
from app.services.user_service import UserService


async def create_admin_accounts():
    """Erstellt Admin- und Test-Accounts mit allen Rechten"""
    
    async for db in get_db():
        try:
            print("🔧 Erstelle Admin- und Test-Accounts...")
            
            # 1. Super-Admin Account
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
                "permissions": {"*": True},  # Alle Berechtigungen
                "language_preference": "de",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Prüfe ob Admin bereits existiert
            existing_admin = await UserService.get_user_by_email(db, admin_data["email"])
            if existing_admin:
                print(f"✅ Admin-Account bereits vorhanden: {admin_data['email']}")
            else:
                admin = User(**admin_data)
                db.add(admin)
                await db.commit()
                await db.refresh(admin)
                print(f"✅ Admin-Account erstellt: {admin_data['email']} (ID: {admin.id})")
            
            # 2. Dienstleister Test-Account
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
            existing_sp = await UserService.get_user_by_email(db, service_provider_data["email"])
            if existing_sp:
                print(f"✅ Dienstleister-Account bereits vorhanden: {service_provider_data['email']}")
            else:
                sp = User(**service_provider_data)
                db.add(sp)
                await db.commit()
                await db.refresh(sp)
                print(f"✅ Dienstleister-Account erstellt: {service_provider_data['email']} (ID: {sp.id})")
            
            # 3. Bauträger Basis Test-Account
            builder_basic_data = {
                "email": "test-bautraeger-basis@buildwise.de",
                "hashed_password": get_password_hash("test1234"),
                "first_name": "Anna",
                "last_name": "Schmidt",
                "phone": "+49 555 123456",
                "user_type": UserType.PRIVATE,
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
                "bio": "Privater Bauherr",
                "region": "Hessen",
                "languages": "Deutsch",
                "roles": ["builder_basic"],
                "permissions": {
                    "view_trades": True,
                    "view_documents": True,
                    "visualize": True
                },
                "language_preference": "de",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Prüfe ob Bauträger Basis bereits existiert
            existing_basic = await UserService.get_user_by_email(db, builder_basic_data["email"])
            if existing_basic:
                print(f"✅ Bauträger Basis-Account bereits vorhanden: {builder_basic_data['email']}")
            else:
                basic = User(**builder_basic_data)
                db.add(basic)
                await db.commit()
                await db.refresh(basic)
                print(f"✅ Bauträger Basis-Account erstellt: {builder_basic_data['email']} (ID: {basic.id})")
            
            # 4. Bauträger Pro Test-Account
            builder_pro_data = {
                "email": "test-bautraeger-pro@buildwise.de",
                "hashed_password": get_password_hash("test1234"),
                "first_name": "Dr. Michael",
                "last_name": "Weber",
                "phone": "+49 777 987654",
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
                "company_name": "Weber Immobilien GmbH",
                "company_address": "Hauptstraße 456, 65432 Großstadt",
                "company_phone": "+49 777 987654",
                "company_website": "https://www.weber-immobilien.de",
                "bio": "Professioneller Bauträger mit umfangreicher Erfahrung",
                "region": "Nordrhein-Westfalen",
                "languages": "Deutsch, Englisch, Französisch",
                "roles": ["builder_pro"],
                "permissions": {
                    "view_trades": True,
                    "create_projects": True,
                    "manage_milestones": True,
                    "view_documents": True,
                    "visualize": True,
                    "manage_quotes": True,
                    "view_analytics": True,
                    "manage_tasks": True,
                    "view_finance": True
                },
                "language_preference": "de",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Prüfe ob Bauträger Pro bereits existiert
            existing_pro = await UserService.get_user_by_email(db, builder_pro_data["email"])
            if existing_pro:
                print(f"✅ Bauträger Pro-Account bereits vorhanden: {builder_pro_data['email']}")
            else:
                pro = User(**builder_pro_data)
                db.add(pro)
                await db.commit()
                await db.refresh(pro)
                print(f"✅ Bauträger Pro-Account erstellt: {builder_pro_data['email']} (ID: {pro.id})")
            
            print("\n🎉 Alle Test-Accounts erfolgreich erstellt!")
            print("\n📋 Account-Übersicht:")
            print("┌─────────────────────────────────────────────────────────────────┐")
            print("│ Admin: admin@buildwise.de / Admin123!                        │")
            print("│ Dienstleister: test-dienstleister@buildwise.de / test1234    │")
            print("│ Bauträger Basis: test-bautraeger-basis@buildwise.de / test1234│")
            print("│ Bauträger Pro: test-bautraeger-pro@buildwise.de / test1234   │")
            print("└─────────────────────────────────────────────────────────────────┘")
            
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der Accounts: {e}")
            await db.rollback()
        finally:
            await db.close()


if __name__ == "__main__":
    asyncio.run(create_admin_accounts()) 