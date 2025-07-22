#!/usr/bin/env python3
"""
Fix: Korrigiere ALLE Enum-Werte in der Datenbank
"""

import asyncio
import sys
import os

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from sqlalchemy import text

async def fix_all_enum_values():
    """Korrigiert alle Enum-Werte in der Datenbank."""
    
    print("🔧 Fix: Korrigiere ALLE Enum-Werte")
    print("=" * 50)
    
    async with engine.begin() as conn:
        try:
            # 1. subscription_plan: basis -> BASIS, pro -> PRO
            print("🔄 Korrigiere subscription_plan...")
            
            result = await conn.execute(text("""
                UPDATE users 
                SET subscription_plan = 'BASIS'
                WHERE subscription_plan = 'basis'
            """))
            print(f"✅ 'basis' -> 'BASIS': {result.rowcount} Zeilen")
            
            result = await conn.execute(text("""
                UPDATE users 
                SET subscription_plan = 'PRO'
                WHERE subscription_plan = 'pro'
            """))
            print(f"✅ 'pro' -> 'PRO': {result.rowcount} Zeilen")
            
            # 2. subscription_status: active -> ACTIVE, inactive -> INACTIVE
            print("\n🔄 Korrigiere subscription_status...")
            
            result = await conn.execute(text("""
                UPDATE users 
                SET subscription_status = 'ACTIVE'
                WHERE subscription_status = 'active'
            """))
            print(f"✅ 'active' -> 'ACTIVE': {result.rowcount} Zeilen")
            
            result = await conn.execute(text("""
                UPDATE users 
                SET subscription_status = 'INACTIVE'
                WHERE subscription_status = 'inactive'
            """))
            print(f"✅ 'inactive' -> 'INACTIVE': {result.rowcount} Zeilen")
            
            # 3. user_type: service_provider -> SERVICE_PROVIDER (einheitlich)
            print("\n🔄 Korrigiere user_type...")
            
            result = await conn.execute(text("""
                UPDATE users 
                SET user_type = 'SERVICE_PROVIDER'
                WHERE user_type = 'service_provider'
            """))
            print(f"✅ 'service_provider' -> 'SERVICE_PROVIDER': {result.rowcount} Zeilen")
            
            # 4. Prüfe korrigierte Werte
            print("\n📊 Korrigierte Werte:")
            print("-" * 40)
            
            # subscription_plan
            result = await conn.execute(text("SELECT DISTINCT subscription_plan FROM users WHERE subscription_plan IS NOT NULL"))
            print("subscription_plan:")
            for row in result:
                print(f"   - '{row[0]}'")
            
            # subscription_status  
            result = await conn.execute(text("SELECT DISTINCT subscription_status FROM users WHERE subscription_status IS NOT NULL"))
            print("subscription_status:")
            for row in result:
                print(f"   - '{row[0]}'")
            
            # user_type
            result = await conn.execute(text("SELECT DISTINCT user_type FROM users WHERE user_type IS NOT NULL"))
            print("user_type:")
            for row in result:
                print(f"   - '{row[0]}'")
            
            # 5. Zeige alle User nach Korrektur
            print("\n📋 Alle User nach Korrektur:")
            result = await conn.execute(text("""
                SELECT id, email, user_role, subscription_plan, subscription_status, user_type
                FROM users 
                ORDER BY id
            """))
            
            for row in result:
                user_id, email, user_role, sub_plan, sub_status, user_type = row
                print(f"ID {user_id}: {email}")
                print(f"  Role: {user_role}, Plan: {sub_plan}, Status: {sub_status}, Type: {user_type}")
            
            print("\n✅ Alle Enum-Werte erfolgreich korrigiert!")
            print("🔄 Backend neu starten für Wirksamkeit...")
            
        except Exception as e:
            print(f"❌ Fehler bei der Enum-Korrektur: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(fix_all_enum_values()) 