#!/usr/bin/env python3
"""
Test-Script für E-Mail-Integration
"""

import asyncio
import sys
import os
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.user_service import UserService
from app.schemas.user import UserCreate
from app.models.user import UserType, SubscriptionPlan


async def test_email_integration():
    """Testet die E-Mail-Integration mit Registrierung und Passwort-Reset"""
    
    print("🧪 Teste E-Mail-Integration...")
    
    async for db in get_db():
        try:
            # Test 1: Benutzerregistrierung mit E-Mail-Verifizierung
            print("\n📝 Teste Benutzerregistrierung...")
            
            test_user_data = UserCreate(
                email="test-email@example.com",
                password="TestPasswort123!",
                first_name="Test",
                last_name="Benutzer",
                phone="+49 123 456789",
                user_type=UserType.PRIVATE,
                subscription_plan=SubscriptionPlan.BASIS,
                data_processing_consent=True,
                privacy_policy_accepted=True,
                terms_accepted=True,
                marketing_consent=False
            )
            
            try:
                user = await UserService.create_user(db, test_user_data)
                print(f"✅ Benutzer erstellt: {user.email}")
                print(f"   Verifizierungs-Token: {user.email_verification_token}")
                print(f"   E-Mail verifiziert: {user.email_verified}")
            except Exception as e:
                print(f"❌ Fehler bei Benutzerregistrierung: {e}")
            
            # Test 2: Passwort-Reset anfordern
            print("\n🔐 Teste Passwort-Reset...")
            
            try:
                success = await UserService.request_password_reset(db, "test-email@example.com")
                if success:
                    print("✅ Passwort-Reset angefordert")
                    
                    # Hole Benutzer und zeige Reset-Token
                    user = await UserService.get_user_by_email(db, "test-email@example.com")
                    if user:
                        print(f"   Reset-Token: {user.password_reset_token}")
                        print(f"   Token gültig bis: {user.password_reset_expires_at}")
                else:
                    print("❌ Passwort-Reset fehlgeschlagen")
            except Exception as e:
                print(f"❌ Fehler bei Passwort-Reset: {e}")
            
            # Test 3: Passwort mit Token zurücksetzen
            print("\n🔄 Teste Passwort-Zurücksetzung...")
            
            try:
                user = await UserService.get_user_by_email(db, "test-email@example.com")
                if user and user.password_reset_token:
                    success = await UserService.reset_password_with_token(
                        db, user.password_reset_token, "NeuesPasswort123!"
                    )
                    if success:
                        print("✅ Passwort erfolgreich zurückgesetzt")
                    else:
                        print("❌ Passwort-Zurücksetzung fehlgeschlagen")
                else:
                    print("❌ Kein Reset-Token gefunden")
            except Exception as e:
                print(f"❌ Fehler bei Passwort-Zurücksetzung: {e}")
            
            # Test 4: E-Mail-Verifizierung
            print("\n✅ Teste E-Mail-Verifizierung...")
            
            try:
                user = await UserService.get_user_by_email(db, "test-email@example.com")
                if user and user.email_verification_token:
                    success = await UserService.verify_email(db, user.email_verification_token)
                    if success:
                        print("✅ E-Mail erfolgreich verifiziert")
                        
                        # Aktualisiere Benutzer-Status
                        user.status = "active"
                        await db.commit()
                    else:
                        print("❌ E-Mail-Verifizierung fehlgeschlagen")
                else:
                    print("❌ Kein Verifizierungs-Token gefunden")
            except Exception as e:
                print(f"❌ Fehler bei E-Mail-Verifizierung: {e}")
            
            print("\n🎉 E-Mail-Integration-Tests abgeschlossen!")
            
        except Exception as e:
            print(f"❌ Allgemeiner Fehler: {e}")
            await db.rollback()
        finally:
            await db.close()


if __name__ == "__main__":
    asyncio.run(test_email_integration()) 