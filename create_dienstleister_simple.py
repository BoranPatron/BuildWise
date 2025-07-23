#!/usr/bin/env python3
"""
Einfaches Skript zur Erstellung des Dienstleister-Users
"""

import asyncio
import sys
import os
import hashlib
import secrets

# Füge das aktuelle Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.user import User, UserType, UserStatus, UserRole
from sqlalchemy import select

def hash_password_simple(password: str) -> str:
    """Einfache Passwort-Hashing ohne bcrypt"""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256()
    hash_obj.update((password + salt).encode('utf-8'))
    return f"sha256${salt}${hash_obj.hexdigest()}"

async def create_dienstleister_simple():
    """Erstellt den Dienstleister-User einfach und direkt"""
    try:
        async for db in get_db():
            email = "test-dienstleister@buildwise.de"
            password = "Dienstleister123!"
            
            print(f"🔍 Erstelle Dienstleister-User: {email}")
            
            # Prüfe ob User bereits existiert
            stmt = select(User).where(User.email == email)
            result = await db.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"✅ User existiert bereits: {existing_user.email}")
                print(f"   User ID: {existing_user.id}")
                print(f"   User Role: {existing_user.user_role}")
                return existing_user
            
            # User erstellen
            hashed_password = hash_password_simple(password)
            
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
            
            try:
                db.add(new_user)
                await db.flush()  # Flush vor commit
                await db.commit()
                await db.refresh(new_user)
                
                print(f"✅ User erfolgreich erstellt!")
                print(f"   User ID: {new_user.id}")
                print(f"   E-Mail: {new_user.email}")
                print(f"   User Role: {new_user.user_role}")
                print(f"   Is Active: {new_user.is_active}")
                print(f"   Passwort: {password}")
                
                return new_user
                
            except Exception as e:
                print(f"❌ Fehler beim Erstellen des Users: {e}")
                await db.rollback()
                return None
                
    except Exception as e:
        print(f"❌ Fehler beim Erstellen des Dienstleisters: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🚀 Erstelle Dienstleister-User (einfach)...")
    print("📧 E-Mail: test-dienstleister@buildwise.de")
    print("🔑 Passwort: Dienstleister123!")
    
    user = asyncio.run(create_dienstleister_simple())
    
    if user:
        print(f"\n🎉 Dienstleister-User erstellt!")
        print(f"💡 Login-Daten für Frontend:")
        print(f"   E-Mail: {user.email}")
        print(f"   Passwort: Dienstleister123!")
        print(f"   User Role: {user.user_role}")
    else:
        print("\n❌ Fehler beim Erstellen des Dienstleister-Users!") 