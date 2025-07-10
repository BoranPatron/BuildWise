#!/usr/bin/env python3
"""
Testskript um den Dienstleister-User zu überprüfen
"""

import asyncio
import sys
import os

# Füge das aktuelle Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.user import User
from app.core.security import verify_password
from sqlalchemy import select

async def check_user():
    """Überprüfe den Dienstleister-User"""
    try:
        # Verwende async/await für die Datenbankverbindung
        async for db in get_db():
            # Verwende select() für asynchrone SQLAlchemy
            stmt = select(User).where(User.email == 'test-dienstleister@buildwise.de')
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user:
                print(f"✅ User gefunden: {user.email}")
                print(f"   User Type: {user.user_type}")
                print(f"   Is Active: {user.is_active}")
                print(f"   Has Consent: {user.has_consent}")
                print(f"   Password Hash: {user.hashed_password[:30]}...")
                
                # Teste Passwort-Verifizierung
                is_valid = verify_password("test1234", user.hashed_password)
                print(f"   Password Valid: {is_valid}")
                
                return user
            else:
                print("❌ User nicht gefunden!")
                return None
                
    except Exception as e:
        print(f"❌ Fehler beim Überprüfen des Users: {e}")
        return None

if __name__ == "__main__":
    print("🔍 Überprüfe Dienstleister-User...")
    user = asyncio.run(check_user())
    
    if user:
        print("\n✅ User ist verfügbar und sollte funktionieren")
    else:
        print("\n❌ User ist nicht verfügbar - Login wird fehlschlagen") 