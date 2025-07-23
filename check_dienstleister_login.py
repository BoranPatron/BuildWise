#!/usr/bin/env python3
"""
Skript um den Status der Dienstleister-Users zu überprüfen
"""

import asyncio
import sys
import os

# Füge das aktuelle Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.user import User
from sqlalchemy import select

async def check_dienstleister_users():
    """Überprüfe den Status der Dienstleister-Users"""
    try:
        async for db in get_db():
            # Prüfe beide möglichen E-Mail-Adressen
            emails_to_check = [
                'dienstleister@buildwise.de',  # Frontend verwendet diese
                'test-dienstleister@buildwise.de'  # Backend-Skripte verwenden diese
            ]
            
            for email in emails_to_check:
                print(f"\n🔍 Prüfe E-Mail: {email}")
                
                stmt = select(User).where(User.email == email)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()
                
                if user:
                    print(f"✅ User gefunden: {user.email}")
                    print(f"   User ID: {user.id}")
                    print(f"   User Type: {user.user_type}")
                    print(f"   User Role: {user.user_role}")
                    print(f"   Is Active: {user.is_active}")
                    print(f"   Status: {user.status}")
                    print(f"   Data Processing Consent: {user.data_processing_consent}")
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
                        print("   ✅ Alle erforderlichen Einwilligungen vorhanden")
                    else:
                        print("   ❌ Fehlende Einwilligungen:")
                        if not user.data_processing_consent:
                            print("      - Datenverarbeitung")
                        if not user.privacy_policy_accepted:
                            print("      - Datenschutzerklärung")
                        if not user.terms_accepted:
                            print("      - AGB")
                    
                    if user.is_active:
                        print("   ✅ User ist aktiv - Login sollte funktionieren")
                    else:
                        print("   ❌ User ist inaktiv - Login wird fehlschlagen")
                        
                    return user
                else:
                    print(f"❌ User nicht gefunden für: {email}")
            
            print("\n❌ Kein Dienstleister-User gefunden!")
            return None
                
    except Exception as e:
        print(f"❌ Fehler beim Überprüfen der User-Status: {e}")
        return None

if __name__ == "__main__":
    print("🔍 Überprüfe Dienstleister-User-Status...")
    user = asyncio.run(check_dienstleister_users())
    
    if user:
        print(f"\n✅ Dienstleister-User gefunden: {user.email}")
        print("💡 Verwende diese E-Mail-Adresse im Frontend!")
    else:
        print("\n❌ Kein Dienstleister-User gefunden!")
        print("💡 Erstelle einen neuen Dienstleister-User mit create_service_provider.py") 