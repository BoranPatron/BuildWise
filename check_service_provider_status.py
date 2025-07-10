#!/usr/bin/env python3
"""
Skript um den Status des Dienstleister-Users zu überprüfen
"""

import asyncio
import sys
import os

# Füge das aktuelle Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.user import User
from sqlalchemy import select

async def check_service_provider_status():
    """Überprüfe den Status des Dienstleister-Users"""
    try:
        async for db in get_db():
            stmt = select(User).where(User.email == 'test-dienstleister@buildwise.de')
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user:
                print(f"✅ User gefunden: {user.email}")
                print(f"   User ID: {user.id}")
                print(f"   User Type: {user.user_type}")
                print(f"   Is Active: {user.is_active}")
                print(f"   Data Processing Consent: {user.data_processing_consent}")
                print(f"   Marketing Consent: {user.marketing_consent}")
                print(f"   Privacy Policy Accepted: {user.privacy_policy_accepted}")
                print(f"   Terms Accepted: {user.terms_accepted}")
                print(f"   Created At: {user.created_at}")
                print(f"   Updated At: {user.updated_at}")
                
                # Prüfe ob alle erforderlichen Einwilligungen vorhanden sind
                required_consents = [
                    user.data_processing_consent,
                    user.privacy_policy_accepted,
                    user.terms_accepted
                ]
                
                if all(required_consents):
                    print("\n✅ Alle erforderlichen Einwilligungen vorhanden")
                else:
                    print("\n❌ Fehlende Einwilligungen:")
                    if not user.data_processing_consent:
                        print("   - Datenverarbeitung")
                    if not user.privacy_policy_accepted:
                        print("   - Datenschutzerklärung")
                    if not user.terms_accepted:
                        print("   - AGB")
                
                if user.is_active:
                    print("\n✅ User ist aktiv - Login sollte funktionieren")
                else:
                    print("\n❌ User ist inaktiv - Login wird fehlschlagen")
                
                return user
            else:
                print("❌ User nicht gefunden!")
                return None
                
    except Exception as e:
        print(f"❌ Fehler beim Überprüfen des User-Status: {e}")
        return None

if __name__ == "__main__":
    print("🔍 Überprüfe Dienstleister-User-Status...")
    user = asyncio.run(check_service_provider_status())
    
    if user:
        print("\n✅ User-Status überprüft")
    else:
        print("\n❌ User-Status konnte nicht überprüft werden") 