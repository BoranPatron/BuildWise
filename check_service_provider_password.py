#!/usr/bin/env python3
"""
Skript um das Passwort des Dienstleister-Users zu überprüfen und zu korrigieren
"""

import asyncio
import sys
import os

# Füge das aktuelle Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.user import User
from app.core.security import verify_password, get_password_hash
from sqlalchemy import select

async def check_and_fix_password():
    """Überprüfe und korrigiere das Passwort des Dienstleister-Users"""
    try:
        # Verwende async/await für die Datenbankverbindung
        async for db in get_db():
            stmt = select(User).where(User.email == 'test-dienstleister@buildwise.de')
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user:
                print(f"✅ User gefunden: {user.email}")
                print(f"   User Type: {user.user_type}")
                print(f"   Is Active: {user.is_active}")
                
                # Teste verschiedene Passwörter
                test_passwords = [
                    "test1234",
                    "Test1234!Secure", 
                    "Test1234Secure",
                    "test1234!",
                    "Test1234"
                ]
                
                print("\n🔍 Teste Passwörter:")
                for password in test_passwords:
                    is_valid = verify_password(password, user.hashed_password)
                    print(f"   '{password}': {'✅' if is_valid else '❌'}")
                
                # Setze das Passwort auf 'test1234' zurück
                print("\n🔧 Setze Passwort auf 'test1234' zurück...")
                user.hashed_password = get_password_hash("test1234")
                db.add(user)
                await db.commit()
                print("✅ Passwort erfolgreich zurückgesetzt!")
                
                # Teste das neue Passwort
                is_valid = verify_password("test1234", user.hashed_password)
                print(f"   Neues Passwort 'test1234': {'✅' if is_valid else '❌'}")
                
                return user
            else:
                print("❌ User nicht gefunden!")
                return None
                
    except Exception as e:
        print(f"❌ Fehler beim Überprüfen des Passworts: {e}")
        return None

if __name__ == "__main__":
    print("🔍 Überprüfe und korrigiere Dienstleister-Passwort...")
    user = asyncio.run(check_and_fix_password())
    
    if user:
        print("\n✅ Passwort wurde korrigiert - Login sollte jetzt funktionieren")
    else:
        print("\n❌ Passwort konnte nicht korrigiert werden") 