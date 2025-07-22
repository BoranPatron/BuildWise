#!/usr/bin/env python3
"""
Diagnose: Enum-Problem bei user_role
"""

import asyncio
import sys
import os

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from sqlalchemy import text

async def diagnose_enum_problem():
    """Diagnostiziert das user_role Enum-Problem."""
    
    print("🔍 Diagnose: UserRole Enum-Problem")
    print("=" * 50)
    
    async with engine.begin() as conn:
        try:
            # Prüfe die Spalten-Definition
            print("📊 Users-Tabelle Schema:")
            result = await conn.execute(text("PRAGMA table_info(users);"))
            
            for row in result:
                if 'user_role' in str(row):
                    print(f"   user_role Spalte: {row}")
            
            # Prüfe aktuelle Werte
            print("\n📋 Aktuelle user_role Werte:")
            result = await conn.execute(text("""
                SELECT id, email, user_role, LENGTH(user_role) as role_length
                FROM users 
                WHERE user_role IS NOT NULL
                ORDER BY id
            """))
            
            for row in result:
                user_id, email, role, length = row
                print(f"   ID {user_id}: {email} -> '{role}' (Länge: {length})")
            
            # Prüfe alle Rollen-Werte
            print("\n🔍 Alle user_role Werte (auch NULL):")
            result = await conn.execute(text("""
                SELECT id, email, user_role
                FROM users 
                ORDER BY id
            """))
            
            for row in result:
                user_id, email, role = row
                print(f"   ID {user_id}: {email} -> '{role}'")
                
            # Versuche einen Test-User zu laden
            print("\n🧪 Test: Lade User mit ID 2:")
            try:
                result = await conn.execute(text("""
                    SELECT id, email, user_role 
                    FROM users 
                    WHERE id = 2
                """))
                
                row = result.fetchone()
                if row:
                    print(f"   ✅ Raw SQL: ID {row[0]}, Email: {row[1]}, Role: '{row[2]}'")
                else:
                    print("   ❌ Kein User mit ID 2 gefunden")
                    
            except Exception as e:
                print(f"   ❌ Fehler beim Raw SQL: {e}")
            
        except Exception as e:
            print(f"❌ Fehler bei der Diagnose: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(diagnose_enum_problem()) 