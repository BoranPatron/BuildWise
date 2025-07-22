#!/usr/bin/env python3
"""
Prüfe alle Enum-Werte in der Datenbank
"""

import asyncio
import sys
import os

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from sqlalchemy import text

async def check_all_enum_values():
    """Prüft alle Enum-Werte in der Datenbank."""
    
    print("🔍 Alle Enum-Felder prüfen:")
    print("=" * 60)
    
    async with engine.begin() as conn:
        try:
            # 1. user_role
            result = await conn.execute(text("SELECT DISTINCT user_role FROM users WHERE user_role IS NOT NULL"))
            print("📋 user_role Werte:")
            for row in result:
                print(f'   - "{row[0]}"')
            
            # 2. subscription_plan
            result = await conn.execute(text("SELECT DISTINCT subscription_plan FROM users WHERE subscription_plan IS NOT NULL"))
            print("\n📋 subscription_plan Werte:")
            for row in result:
                print(f'   - "{row[0]}"')
            
            # 3. subscription_status
            result = await conn.execute(text("SELECT DISTINCT subscription_status FROM users WHERE subscription_status IS NOT NULL"))
            print("\n📋 subscription_status Werte:")
            for row in result:
                print(f'   - "{row[0]}"')
            
            # 4. user_type
            result = await conn.execute(text("SELECT DISTINCT user_type FROM users WHERE user_type IS NOT NULL"))
            print("\n📋 user_type Werte:")
            for row in result:
                print(f'   - "{row[0]}"')
            
            # 5. Zeige Problem-Users
            print("\n📋 Problematische User:")
            result = await conn.execute(text("""
                SELECT id, email, user_role, subscription_plan, subscription_status, user_type
                FROM users 
                ORDER BY id
            """))
            
            for row in result:
                user_id, email, user_role, sub_plan, sub_status, user_type = row
                print(f"   ID {user_id}: {email}")
                print(f"     user_role: '{user_role}'")
                print(f"     subscription_plan: '{sub_plan}'")
                print(f"     subscription_status: '{sub_status}'")
                print(f"     user_type: '{user_type}'")
                print()
                
        except Exception as e:
            print(f"❌ Fehler bei der Enum-Prüfung: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(check_all_enum_values()) 