#!/usr/bin/env python3
"""
Skript zur Erstellung eines Test-Benutzers für API-Tests
"""

import asyncio
import aiosqlite
from datetime import datetime
from passlib.context import CryptContext

# Passwort-Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_test_user():
    """Erstellt einen Test-Benutzer mit bekanntem Passwort"""
    
    async with aiosqlite.connect('buildwise.db') as db:
        print("🔧 Verbunden zur SQLite-Datenbank")
        
        # Prüfe ob der Test-Benutzer bereits existiert
        cursor = await db.execute("""
            SELECT id, email FROM users WHERE email = ?
        """, ("test@buildwise.de",))
        existing_user = await cursor.fetchone()
        
        if existing_user:
            print(f"⚠️ Test-Benutzer existiert bereits: ID={existing_user[0]}, Email={existing_user[1]}")
            
            # Ändere das Passwort
            hashed_password = pwd_context.hash("test123")
            await db.execute("""
                UPDATE users SET hashed_password = ? WHERE email = ?
            """, (hashed_password, "test@buildwise.de"))
            await db.commit()
            print("✅ Passwort für existierenden Test-Benutzer aktualisiert")
            return
        
        # Erstelle neuen Test-Benutzer
        hashed_password = pwd_context.hash("test123")
        
        test_user = {
            'email': 'test@buildwise.de',
            'first_name': 'Test',
            'last_name': 'Bautraeger',
            'password_hash': hashed_password,
            'user_type': 'PRIVATE',
            'is_active': True,
            'data_processing_consent': True,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        try:
            cursor = await db.execute("""
                INSERT INTO users (
                    email, first_name, last_name, hashed_password, user_type, 
                    is_active, data_processing_consent, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                test_user['email'],
                test_user['first_name'],
                test_user['last_name'],
                test_user['password_hash'],
                test_user['user_type'],
                test_user['is_active'],
                test_user['data_processing_consent'],
                test_user['created_at'],
                test_user['updated_at']
            ))
            
            await db.commit()
            print("✅ Test-Benutzer erfolgreich erstellt!")
            print(f"📋 Email: {test_user['email']}")
            print(f"📋 Passwort: test123")
            
        except Exception as e:
            print(f"❌ Fehler beim Erstellen des Test-Benutzers: {e}")

if __name__ == "__main__":
    asyncio.run(create_test_user()) 