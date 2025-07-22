#!/usr/bin/env python3
"""
Migration: Füge Subscription-Felder hinzu
"""

import asyncio
import sys
import os

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from sqlalchemy import text

async def add_subscription_columns():
    """Fügt die neuen Subscription-Felder zur users Tabelle hinzu."""
    
    print("🚀 Füge Subscription-Felder hinzu...")
    print("=" * 60)
    
    async with engine.begin() as conn:
        try:
            # Für SQLite: Prüfe ob Spalten bereits existieren
            result = await conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result]
            
            subscription_columns = [
                'subscription_plan', 'subscription_status', 'subscription_id',
                'customer_id', 'subscription_start', 'subscription_end', 'max_gewerke'
            ]
            
            # Füge subscription_plan hinzu
            if 'subscription_plan' not in columns:
                await conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN subscription_plan VARCHAR(10) DEFAULT 'basis'
                """))
                print("✅ Spalte 'subscription_plan' hinzugefügt")
            else:
                print("ℹ️ Spalte 'subscription_plan' existiert bereits")
            
            # Füge subscription_status hinzu
            if 'subscription_status' not in columns:
                await conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN subscription_status VARCHAR(20) DEFAULT 'inactive'
                """))
                print("✅ Spalte 'subscription_status' hinzugefügt")
            else:
                print("ℹ️ Spalte 'subscription_status' existiert bereits")
            
            # Füge subscription_id hinzu
            if 'subscription_id' not in columns:
                await conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN subscription_id VARCHAR(255)
                """))
                print("✅ Spalte 'subscription_id' hinzugefügt")
            else:
                print("ℹ️ Spalte 'subscription_id' existiert bereits")
            
            # Füge customer_id hinzu
            if 'customer_id' not in columns:
                await conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN customer_id VARCHAR(255)
                """))
                print("✅ Spalte 'customer_id' hinzugefügt")
            else:
                print("ℹ️ Spalte 'customer_id' existiert bereits")
            
            # Füge subscription_start hinzu
            if 'subscription_start' not in columns:
                await conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN subscription_start TIMESTAMP
                """))
                print("✅ Spalte 'subscription_start' hinzugefügt")
            else:
                print("ℹ️ Spalte 'subscription_start' existiert bereits")
            
            # Füge subscription_end hinzu
            if 'subscription_end' not in columns:
                await conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN subscription_end TIMESTAMP
                """))
                print("✅ Spalte 'subscription_end' hinzugefügt")
            else:
                print("ℹ️ Spalte 'subscription_end' existiert bereits")
            
            # Füge max_gewerke hinzu
            if 'max_gewerke' not in columns:
                await conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN max_gewerke INTEGER DEFAULT 3
                """))
                print("✅ Spalte 'max_gewerke' hinzugefügt")
            else:
                print("ℹ️ Spalte 'max_gewerke' existiert bereits")
            
            # Erstelle Indices für Performance
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_subscription 
                ON users(subscription_plan, subscription_status)
            """))
            print("✅ Index 'idx_users_subscription' erstellt")
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_customer 
                ON users(customer_id)
            """))
            print("✅ Index 'idx_users_customer' erstellt")
            
            # Setze Defaults für bestehende Benutzer
            await conn.execute(text("""
                UPDATE users 
                SET subscription_plan = 'BASIS',
                    subscription_status = 'INACTIVE',
                    max_gewerke = 3
                WHERE subscription_plan IS NULL
            """))
            print("✅ Standard-Werte für bestehende Benutzer gesetzt")
            
            # Admins bekommen Pro-Plan
            await conn.execute(text("""
                UPDATE users 
                SET subscription_plan = 'PRO',
                    subscription_status = 'ACTIVE',
                    max_gewerke = -1
                WHERE user_role = 'admin'
            """))
            print("✅ Admin-Benutzer auf Pro-Plan gesetzt")
            
            print("\n✅ Subscription-Migration erfolgreich abgeschlossen!")
            
        except Exception as e:
            print(f"❌ Fehler bei der Migration: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(add_subscription_columns()) 