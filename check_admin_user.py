#!/usr/bin/env python3
"""
Script zur Überprüfung und Reparatur des Admin-Users
"""

import asyncio
import sys
import os
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.user import User, UserType, SubscriptionPlan, UserStatus
from app.core.security import get_password_hash, verify_password
from app.services.user_service import UserService


async def check_and_fix_admin_user():
    """Überprüft und repariert den Admin-User"""
    
    async for db in get_db():
        try:
            print("🔍 Überprüfe Admin-User...")
            
            # Suche nach Admin-User
            result = await db.execute(select(User).where(User.email == "admin@buildwise.de"))
            admin_user = result.scalar_one_or_none()
            
            if not admin_user:
                print("❌ Admin-User nicht gefunden. Erstelle neuen Admin-User...")
                
                # Erstelle neuen Admin-User
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
                    "updated_at": datetime.utcnow()
                }
                
                admin_user = User(**admin_data)
                db.add(admin_user)
                await db.commit()
                await db.refresh(admin_user)
                print(f"✅ Neuer Admin-User erstellt: {admin_user.email} (ID: {admin_user.id})")
                
            else:
                print(f"✅ Admin-User gefunden: {admin_user.email} (ID: {admin_user.id})")
                
                # Überprüfe und repariere fehlende Felder
                needs_update = False
                
                # Prüfe DSGVO-Felder
                if not hasattr(admin_user, 'data_processing_consent') or admin_user.data_processing_consent is None:
                    admin_user.data_processing_consent = True
                    needs_update = True
                
                if not hasattr(admin_user, 'marketing_consent') or admin_user.marketing_consent is None:
                    admin_user.marketing_consent = True
                    needs_update = True
                
                if not hasattr(admin_user, 'privacy_policy_accepted') or admin_user.privacy_policy_accepted is None:
                    admin_user.privacy_policy_accepted = True
                    needs_update = True
                
                if not hasattr(admin_user, 'terms_accepted') or admin_user.terms_accepted is None:
                    admin_user.terms_accepted = True
                    needs_update = True
                
                # Prüfe E-Mail-Verifizierung
                if not hasattr(admin_user, 'email_verified') or not admin_user.email_verified:
                    admin_user.email_verified = True
                    admin_user.email_verified_at = datetime.utcnow()
                    needs_update = True
                
                # Prüfe Subscription-Felder
                if not hasattr(admin_user, 'subscription_plan'):
                    admin_user.subscription_plan = SubscriptionPlan.PRO
                    needs_update = True
                
                if not hasattr(admin_user, 'subscription_active') or admin_user.subscription_active is None:
                    admin_user.subscription_active = True
                    needs_update = True
                
                # Prüfe Rollen und Berechtigungen
                if not hasattr(admin_user, 'roles') or not admin_user.roles:
                    admin_user.roles = ["admin"]
                    needs_update = True
                
                if not hasattr(admin_user, 'permissions') or not admin_user.permissions:
                    admin_user.permissions = {"*": True}
                    needs_update = True
                
                # Prüfe Status
                if not hasattr(admin_user, 'status') or admin_user.status != UserStatus.ACTIVE:
                    admin_user.status = UserStatus.ACTIVE
                    needs_update = True
                
                if needs_update:
                    admin_user.updated_at = datetime.utcnow()
                    await db.commit()
                    print("✅ Admin-User repariert")
                else:
                    print("✅ Admin-User ist korrekt konfiguriert")
                
                # Teste Passwort
                test_password = "Admin123!"
                if verify_password(test_password, admin_user.hashed_password):
                    print("✅ Passwort ist korrekt")
                else:
                    print("❌ Passwort ist falsch. Setze Passwort zurück...")
                    admin_user.hashed_password = get_password_hash(test_password)
                    admin_user.updated_at = datetime.utcnow()
                    await db.commit()
                    print("✅ Passwort zurückgesetzt")
            
            # Zeige Admin-User Details
            print(f"\n📋 Admin-User Details:")
            print(f"   E-Mail: {admin_user.email}")
            print(f"   Status: {admin_user.status}")
            print(f"   E-Mail verifiziert: {admin_user.email_verified}")
            print(f"   DSGVO-Einwilligung: {admin_user.data_processing_consent}")
            print(f"   Subscription aktiv: {admin_user.subscription_active}")
            print(f"   Rollen: {admin_user.roles}")
            print(f"   Berechtigungen: {admin_user.permissions}")
            
        except Exception as e:
            print(f"❌ Fehler: {e}")
            await db.rollback()
        finally:
            await db.close()


if __name__ == "__main__":
    asyncio.run(check_and_fix_admin_user()) 