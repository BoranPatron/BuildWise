#!/usr/bin/env python3
"""
Fix: Setze user_role und role_selected für bestehende Benutzer
"""

import asyncio
import sys
import os

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from sqlalchemy import text

async def fix_existing_user_roles():
    """Korrigiert user_role und role_selected für bestehende Benutzer."""
    
    print("🚀 Korrigiere bestehende User-Rollen...")
    print("=" * 60)
    
    async with engine.begin() as conn:
        try:
            # Setze Dienstleister-Rolle für bestehende Service Provider (beide Varianten)
            result1 = await conn.execute(text("""
                UPDATE users 
                SET user_role = 'DIENSTLEISTER',
                    role_selected = 1,
                    role_selected_at = datetime('now')
                WHERE user_type = 'service_provider' 
                AND (user_role IS NULL OR role_selected = 0)
            """))
            
            result2 = await conn.execute(text("""
                UPDATE users 
                SET user_role = 'DIENSTLEISTER',
                    role_selected = 1,
                    role_selected_at = datetime('now')
                WHERE user_type = 'SERVICE_PROVIDER' 
                AND (user_role IS NULL OR role_selected = 0)
            """))
            
            total_dienstleister = result1.rowcount + result2.rowcount
            print(f"✅ Dienstleister-Rollen gesetzt für {total_dienstleister} Benutzer")
            
            # Setze Admin-Rolle für Admin-Benutzer
            result = await conn.execute(text("""
                UPDATE users 
                SET user_role = 'ADMIN',
                    role_selected = 1,
                    role_selected_at = datetime('now')
                WHERE email LIKE '%admin%' 
                AND (user_role IS NULL OR role_selected = 0)
            """))
            print(f"✅ Admin-Rollen gesetzt für {result.rowcount} Benutzer")
            
            # Zeige aktuellen Status aller Benutzer
            result = await conn.execute(text("""
                SELECT id, email, user_type, user_role, role_selected, subscription_plan
                FROM users 
                ORDER BY id
            """))
            
            print("\n📊 Aktueller Status aller Benutzer:")
            print("-" * 80)
            print(f"{'ID':<3} {'Email':<30} {'UserType':<15} {'UserRole':<12} {'Selected':<8} {'Plan':<10}")
            print("-" * 80)
            
            for row in result:
                user_id, email, user_type, user_role, role_selected, subscription_plan = row
                print(f"{user_id:<3} {email:<30} {user_type or 'None':<15} {user_role or 'None':<12} {bool(role_selected):<8} {subscription_plan or 'None':<10}")
            
            print("\n✅ User-Rollen-Korrektur abgeschlossen!")
            
        except Exception as e:
            print(f"❌ Fehler bei der Korrektur: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(fix_existing_user_roles()) 