#!/usr/bin/env python3
"""
Fix: Korrigiere Enum-Werte in der Datenbank
"""

import asyncio
import sys
import os

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from sqlalchemy import text

async def fix_enum_values():
    """Korrigiert die Enum-Werte in der Datenbank."""
    
    print("🔧 Fix: Korrigiere Enum-Werte in der Datenbank")
    print("=" * 50)
    
    async with engine.begin() as conn:
        try:
            # Prüfe aktuelle Werte
            print("📋 Aktuelle user_role Werte:")
            result = await conn.execute(text("""
                SELECT id, email, user_role
                FROM users 
                WHERE user_role IS NOT NULL
                ORDER BY id
            """))
            
            for row in result:
                user_id, email, role = row
                print(f"   ID {user_id}: {email} -> '{role}'")
            
            # Korrigiere die problematischen Werte
            print("\n🔄 Korrigiere Enum-Werte...")
            
            # 1. Korrigiere 'dienstleister' zu 'DIENSTLEISTER'
            result = await conn.execute(text("""
                UPDATE users 
                SET user_role = 'DIENSTLEISTER'
                WHERE user_role = 'dienstleister'
            """))
            print(f"✅ 'dienstleister' -> 'DIENSTLEISTER': {result.rowcount} Zeilen")
            
            # 2. Korrigiere 'admin' zu 'ADMIN'
            result = await conn.execute(text("""
                UPDATE users 
                SET user_role = 'ADMIN'
                WHERE user_role = 'admin'
            """))
            print(f"✅ 'admin' -> 'ADMIN': {result.rowcount} Zeilen")
            
            # 3. Korrigiere 'bautraeger' zu 'BAUTRAEGER' (falls vorhanden)
            result = await conn.execute(text("""
                UPDATE users 
                SET user_role = 'BAUTRAEGER'
                WHERE user_role = 'bautraeger'
            """))
            print(f"✅ 'bautraeger' -> 'BAUTRAEGER': {result.rowcount} Zeilen")
            
            # Prüfe korrigierte Werte
            print("\n📋 Korrigierte user_role Werte:")
            result = await conn.execute(text("""
                SELECT id, email, user_role
                FROM users 
                WHERE user_role IS NOT NULL
                ORDER BY id
            """))
            
            for row in result:
                user_id, email, role = row
                print(f"   ID {user_id}: {email} -> '{role}'")
            
            print("\n✅ Enum-Werte erfolgreich korrigiert!")
            print("🔄 Backend neu starten für Wirksamkeit...")
            
        except Exception as e:
            print(f"❌ Fehler bei der Enum-Korrektur: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(fix_enum_values()) 