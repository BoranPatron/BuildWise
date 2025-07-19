#!/usr/bin/env python3
"""
Script zur Reparatur des Admin-Users mit SQL
"""

import asyncio
import sys
import os
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from sqlalchemy import text


async def fix_admin_user():
    """Repariert den Admin-User mit SQL-Updates"""
    
    async for db in get_db():
        try:
            print("🔧 Repariere Admin-User...")
            
            # SQL-Updates für Admin-User
            update_queries = [
                """
                UPDATE users 
                SET 
                    email_verified = true,
                    email_verified_at = CURRENT_TIMESTAMP,
                    data_processing_consent = true,
                    marketing_consent = true,
                    privacy_policy_accepted = true,
                    terms_accepted = true,
                    subscription_active = true,
                    subscription_plan = 'pro',
                    status = 'active',
                    is_active = true,
                    is_verified = true,
                    roles = '["admin"]',
                    permissions = '{"*": true}',
                    language_preference = 'de',
                    updated_at = CURRENT_TIMESTAMP
                WHERE email = 'admin@buildwise.de'
                """,
                
                """
                SELECT 
                    id,
                    email,
                    first_name,
                    last_name,
                    email_verified,
                    data_processing_consent,
                    subscription_active,
                    status,
                    roles,
                    permissions
                FROM users 
                WHERE email = 'admin@buildwise.de'
                """
            ]
            
            # Führe Updates aus
            for i, query in enumerate(update_queries):
                if i == 0:  # Update-Query
                    result = await db.execute(text(query))
                    await db.commit()
                    print(f"✅ Update {i+1} ausgeführt")
                else:  # Select-Query
                    result = await db.execute(text(query))
                    rows = result.fetchall()
                    
                    if rows:
                        print("\n📋 Admin-User Details:")
                        for row in rows:
                            print(f"   ID: {row[0]}")
                            print(f"   E-Mail: {row[1]}")
                            print(f"   Name: {row[2]} {row[3]}")
                            print(f"   E-Mail verifiziert: {row[4]}")
                            print(f"   DSGVO-Einwilligung: {row[5]}")
                            print(f"   Subscription aktiv: {row[6]}")
                            print(f"   Status: {row[7]}")
                            print(f"   Rollen: {row[8]}")
                            print(f"   Berechtigungen: {row[9]}")
                    else:
                        print("❌ Admin-User nicht gefunden!")
            
            print("\n🎉 Admin-User Reparatur abgeschlossen!")
            
        except Exception as e:
            print(f"❌ Fehler: {e}")
            await db.rollback()
        finally:
            await db.close()


if __name__ == "__main__":
    asyncio.run(fix_admin_user()) 