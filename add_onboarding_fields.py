#!/usr/bin/env python3
"""
Migration: Füge Onboarding-Felder für Erstbenutzer-Erkennung hinzu
"""

import asyncio
import sys
import os

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from sqlalchemy import text

async def add_onboarding_fields():
    """Fügt Onboarding-Felder zur users Tabelle hinzu."""
    
    print("🔧 Migration: Onboarding-Felder hinzufügen")
    print("=" * 50)
    
    async with engine.begin() as conn:
        try:
            # 1. Füge neue Spalten hinzu
            print("📋 Füge neue Onboarding-Spalten hinzu...")
            
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN first_login_completed BOOLEAN DEFAULT FALSE
            """))
            print("✅ first_login_completed hinzugefügt")
            
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN onboarding_completed BOOLEAN DEFAULT FALSE
            """))
            print("✅ onboarding_completed hinzugefügt")
            
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN onboarding_step INTEGER DEFAULT 0
            """))
            print("✅ onboarding_step hinzugefügt")
            
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN onboarding_started_at DATETIME
            """))
            print("✅ onboarding_started_at hinzugefügt")
            
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN onboarding_completed_at DATETIME
            """))
            print("✅ onboarding_completed_at hinzugefügt")
            
            # 2. Setze bestehende User als "bereits onboarded"
            print("\n🔄 Migriere bestehende User...")
            
            # User mit Rolle = bereits onboarded
            result = await conn.execute(text("""
                UPDATE users 
                SET first_login_completed = 1,
                    onboarding_completed = 1,
                    onboarding_step = 999,
                    onboarding_completed_at = datetime('now')
                WHERE role_selected = 1 AND user_role IS NOT NULL
            """))
            print(f"✅ {result.rowcount} User mit Rolle als 'onboarded' markiert")
            
            # Admin-User = bereits onboarded
            result = await conn.execute(text("""
                UPDATE users 
                SET first_login_completed = 1,
                    onboarding_completed = 1,
                    onboarding_step = 999,
                    onboarding_completed_at = datetime('now')
                WHERE user_role = 'ADMIN'
            """))
            print(f"✅ {result.rowcount} Admin-User als 'onboarded' markiert")
            
            # Service Provider = bereits onboarded (automatische Rolle)
            result = await conn.execute(text("""
                UPDATE users 
                SET first_login_completed = 1,
                    onboarding_completed = 1,
                    onboarding_step = 999,
                    onboarding_completed_at = datetime('now')
                WHERE user_type = 'SERVICE_PROVIDER' AND user_role = 'DIENSTLEISTER'
            """))
            print(f"✅ {result.rowcount} Service Provider als 'onboarded' markiert")
            
            # 3. Prüfe Ergebnis
            print("\n📊 Migration-Ergebnis:")
            result = await conn.execute(text("""
                SELECT 
                    COUNT(*) as total_users,
                    SUM(CASE WHEN first_login_completed = 1 THEN 1 ELSE 0 END) as completed_first_login,
                    SUM(CASE WHEN onboarding_completed = 1 THEN 1 ELSE 0 END) as completed_onboarding,
                    SUM(CASE WHEN first_login_completed = 0 THEN 1 ELSE 0 END) as needs_onboarding
                FROM users
            """))
            
            row = result.fetchone()
            total, first_login, onboarded, needs = row
            
            print(f"  📈 Gesamt User: {total}")
            print(f"  ✅ Ersten Login abgeschlossen: {first_login}")
            print(f"  ✅ Onboarding abgeschlossen: {onboarded}")
            print(f"  🎯 Benötigt Onboarding: {needs}")
            
            # 4. Zeige User die Onboarding benötigen
            if needs > 0:
                print("\n👥 User die Onboarding benötigen:")
                result = await conn.execute(text("""
                    SELECT id, email, user_role, role_selected
                    FROM users 
                    WHERE first_login_completed = 0
                    ORDER BY id
                """))
                
                for row in result:
                    user_id, email, role, selected = row
                    print(f"  ID {user_id}: {email} (Role: {role}, Selected: {bool(selected)})")
            
            print("\n✅ Onboarding-Felder erfolgreich hinzugefügt!")
            
        except Exception as e:
            print(f"❌ Fehler bei der Migration: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(add_onboarding_fields()) 