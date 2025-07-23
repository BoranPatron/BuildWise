#!/usr/bin/env python3
"""
Debug-Skript für Login-Probleme
"""

import asyncio
import sys
import os

# Füge das aktuelle Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.user import User
from app.services.security_service import SecurityService
from sqlalchemy import select

async def debug_login():
    """Debug-Login-Problem"""
    try:
        async for db in get_db():
            email = "test-dienstleister@buildwise.de"
            password = "Dienstleister123!"
            
            print(f"🔍 Debug-Login für: {email}")
            print(f"🔑 Passwort: {password}")
            
            # 1. Prüfe ob User existiert
            stmt = select(User).where(User.email == email)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                print("❌ User nicht gefunden!")
                print("💡 Erstelle User...")
                
                # User erstellen
                hashed_password = SecurityService.hash_password(password)
                
                from app.models.user import UserType, UserStatus, UserRole
                
                new_user = User(
                    email=email,
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
                
                db.add(new_user)
                await db.commit()
                await db.refresh(new_user)
                
                print(f"✅ User erstellt: {new_user.email}")
                user = new_user
            else:
                print(f"✅ User gefunden: {user.email}")
                print(f"   User ID: {user.id}")
                print(f"   User Role: {user.user_role}")
                print(f"   Is Active: {user.is_active}")
                print(f"   Status: {user.status}")
                print(f"   Data Processing Consent: {user.data_processing_consent}")
                print(f"   Privacy Policy Accepted: {user.privacy_policy_accepted}")
                print(f"   Terms Accepted: {user.terms_accepted}")
            
            # 2. Prüfe Passwort
            print(f"\n🔐 Prüfe Passwort...")
            hashed_password = getattr(user, 'hashed_password', '')
            print(f"   Hashed Password: {hashed_password[:20]}...")
            
            is_valid = SecurityService.verify_password(password, str(hashed_password))
            print(f"   Passwort korrekt: {is_valid}")
            
            # 3. Prüfe alle Login-Bedingungen
            print(f"\n📋 Login-Bedingungen:")
            print(f"   User existiert: ✅")
            print(f"   User ist aktiv: {user.is_active}")
            print(f"   Data Processing Consent: {user.data_processing_consent}")
            print(f"   Privacy Policy Accepted: {user.privacy_policy_accepted}")
            print(f"   Terms Accepted: {user.terms_accepted}")
            
            # 4. Simuliere Login
            if user.is_active and user.data_processing_consent and user.privacy_policy_accepted and user.terms_accepted and is_valid:
                print(f"\n🎉 Login sollte funktionieren!")
                print(f"📧 E-Mail: {user.email}")
                print(f"🔑 Passwort: {password}")
                print(f"👤 User Role: {user.user_role}")
            else:
                print(f"\n❌ Login wird fehlschlagen!")
                if not user.is_active:
                    print("   - User ist nicht aktiv")
                if not user.data_processing_consent:
                    print("   - Data Processing Consent fehlt")
                if not user.privacy_policy_accepted:
                    print("   - Privacy Policy nicht akzeptiert")
                if not user.terms_accepted:
                    print("   - Terms nicht akzeptiert")
                if not is_valid:
                    print("   - Passwort ist falsch")
            
            return user
                
    except Exception as e:
        print(f"❌ Fehler beim Debug-Login: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🔧 Debug-Login-Problem...")
    user = asyncio.run(debug_login())
    
    if user:
        print(f"\n✅ Debug abgeschlossen!")
        print(f"💡 Verwende diese Anmeldedaten im Frontend:")
        print(f"   E-Mail: {user.email}")
        print(f"   Passwort: Dienstleister123!")
    else:
        print("\n❌ Debug fehlgeschlagen!") 