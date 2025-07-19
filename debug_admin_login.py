#!/usr/bin/env python3
"""
Debug-Script für Admin-Login
"""

import asyncio
import sys
import os
from datetime import datetime, date

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.user import User, UserType, SubscriptionPlan, UserStatus
from app.core.security import get_password_hash, verify_password
from sqlalchemy import select


async def debug_admin_login():
    """Debuggt den Admin-Login"""
    
    async for db in get_db():
        try:
            print("🔍 Debug Admin-Login...")
            
            # Suche nach Admin-User
            result = await db.execute(select(User).where(User.email == "admin@buildwise.de"))
            admin_user = result.scalar_one_or_none()
            
            if not admin_user:
                print("❌ Admin-User nicht gefunden!")
                return
            
            print(f"✅ Admin-User gefunden: {admin_user.email}")
            
            # Teste Passwort
            test_password = "Admin123!"
            password_correct = verify_password(test_password, admin_user.hashed_password)
            print(f"🔐 Passwort korrekt: {password_correct}")
            
            # Prüfe alle Login-Bedingungen
            print("\n📋 Login-Bedingungen:")
            print(f"   is_active: {admin_user.is_active}")
            print(f"   email_verified: {admin_user.email_verified}")
            print(f"   data_processing_consent: {admin_user.data_processing_consent}")
            print(f"   subscription_active: {admin_user.subscription_active}")
            print(f"   status: {admin_user.status}")
            
            # Prüfe fehlende Felder
            missing_fields = []
            
            if not hasattr(admin_user, 'email_verified') or admin_user.email_verified is None:
                missing_fields.append('email_verified')
            
            if not hasattr(admin_user, 'data_processing_consent') or admin_user.data_processing_consent is None:
                missing_fields.append('data_processing_consent')
            
            if not hasattr(admin_user, 'subscription_active') or admin_user.subscription_active is None:
                missing_fields.append('subscription_active')
            
            if not hasattr(admin_user, 'status') or admin_user.status is None:
                missing_fields.append('status')
            
            if missing_fields:
                print(f"❌ Fehlende Felder: {missing_fields}")
                
                # Repariere fehlende Felder
                print("🔧 Repariere fehlende Felder...")
                
                if 'email_verified' in missing_fields:
                    admin_user.email_verified = True
                    admin_user.email_verified_at = datetime.utcnow()
                
                if 'data_processing_consent' in missing_fields:
                    admin_user.data_processing_consent = True
                
                if 'subscription_active' in missing_fields:
                    admin_user.subscription_active = True
                
                if 'status' in missing_fields:
                    admin_user.status = UserStatus.ACTIVE
                
                # Setze Standard-Rollen und Berechtigungen
                if not hasattr(admin_user, 'roles') or not admin_user.roles:
                    admin_user.roles = ["admin"]
                
                if not hasattr(admin_user, 'permissions') or not admin_user.permissions:
                    admin_user.permissions = {"*": True}
                
                # Setze DSGVO-Einwilligungen
                if not hasattr(admin_user, 'marketing_consent') or admin_user.marketing_consent is None:
                    admin_user.marketing_consent = True
                
                if not hasattr(admin_user, 'privacy_policy_accepted') or admin_user.privacy_policy_accepted is None:
                    admin_user.privacy_policy_accepted = True
                
                if not hasattr(admin_user, 'terms_accepted') or admin_user.terms_accepted is None:
                    admin_user.terms_accepted = True
                
                # Setze Subscription-Plan
                if not hasattr(admin_user, 'subscription_plan'):
                    admin_user.subscription_plan = SubscriptionPlan.PRO
                
                admin_user.updated_at = datetime.utcnow()
                await db.commit()
                print("✅ Admin-User repariert")
                
                # Zeige aktualisierte Werte
                print("\n📋 Aktualisierte Werte:")
                print(f"   email_verified: {admin_user.email_verified}")
                print(f"   data_processing_consent: {admin_user.data_processing_consent}")
                print(f"   subscription_active: {admin_user.subscription_active}")
                print(f"   status: {admin_user.status}")
                print(f"   roles: {admin_user.roles}")
                print(f"   permissions: {admin_user.permissions}")
            else:
                print("✅ Alle Felder sind korrekt")
            
            # Teste Login-Simulation
            print("\n🧪 Login-Simulation:")
            
            # 1. Authentifizierung
            if not password_correct:
                print("❌ Authentifizierung fehlgeschlagen")
                return
            
            print("✅ Authentifizierung erfolgreich")
            
            # 2. Benutzer aktiv
            if not admin_user.is_active:
                print("❌ Benutzer ist nicht aktiv")
                return
            
            print("✅ Benutzer ist aktiv")
            
            # 3. E-Mail verifiziert
            if not admin_user.email_verified:
                print("❌ E-Mail nicht verifiziert")
                return
            
            print("✅ E-Mail verifiziert")
            
            # 4. DSGVO-Einwilligung
            if not admin_user.data_processing_consent:
                print("❌ DSGVO-Einwilligung fehlt")
                return
            
            print("✅ DSGVO-Einwilligung vorhanden")
            
            # 5. Subscription aktiv
            if not admin_user.subscription_active:
                print("❌ Subscription nicht aktiv")
                return
            
            print("✅ Subscription aktiv")
            
            print("\n🎉 Login würde erfolgreich sein!")
            
        except Exception as e:
            print(f"❌ Fehler: {e}")
            await db.rollback()
        finally:
            await db.close()


if __name__ == "__main__":
    asyncio.run(debug_admin_login()) 