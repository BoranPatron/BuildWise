#!/usr/bin/env python3
"""
Migration: Erstellt das BuildWise Credit-System
Datum: 2025-01-27
Beschreibung: Erstellt alle Tabellen für das Credit-System (UserCredits, CreditEvents, CreditPurchases)
"""

import asyncio
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

async def create_credit_system_tables():
    """Erstellt alle Tabellen für das Credit-System"""
    
    print("🚀 MIGRATION: Erstelle Credit-System Tabellen...")
    
    # Verwende SQLite für die Entwicklung
    DATABASE_URL = "sqlite+aiosqlite:///./buildwise.db"
    
    try:
        # Erstelle Engine
        engine = create_async_engine(DATABASE_URL, echo=False)
        
        async with engine.begin() as conn:
            # 1. Erstelle user_credits Tabelle
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_credits (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL UNIQUE,
                    credits INTEGER NOT NULL DEFAULT 100,
                    plan_status VARCHAR(20) NOT NULL DEFAULT 'pro',
                    pro_start_date DATETIME,
                    last_pro_day DATETIME,
                    total_pro_days INTEGER NOT NULL DEFAULT 0,
                    auto_downgrade_enabled BOOLEAN NOT NULL DEFAULT 1,
                    low_credit_warning_sent BOOLEAN NOT NULL DEFAULT 0,
                    downgrade_notification_sent BOOLEAN NOT NULL DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """))
            print("✅ user_credits Tabelle erstellt")
            
            # 2. Erstelle credit_events Tabelle
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS credit_events (
                    id INTEGER PRIMARY KEY,
                    user_credits_id INTEGER NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    credits_change INTEGER NOT NULL,
                    credits_before INTEGER NOT NULL,
                    credits_after INTEGER NOT NULL,
                    description TEXT,
                    related_entity_type VARCHAR(50),
                    related_entity_id INTEGER,
                    stripe_payment_intent_id VARCHAR(255),
                    stripe_session_id VARCHAR(255),
                    ip_address VARCHAR(45),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_credits_id) REFERENCES user_credits (id) ON DELETE CASCADE
                )
            """))
            print("✅ credit_events Tabelle erstellt")
            
            # 3. Erstelle credit_purchases Tabelle
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS credit_purchases (
                    id INTEGER PRIMARY KEY,
                    user_credits_id INTEGER NOT NULL,
                    package_type VARCHAR(20) NOT NULL,
                    credits_amount INTEGER NOT NULL,
                    price_chf REAL NOT NULL,
                    stripe_session_id VARCHAR(255) NOT NULL UNIQUE,
                    stripe_payment_intent_id VARCHAR(255),
                    stripe_customer_id VARCHAR(255),
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    purchased_at DATETIME,
                    completed_at DATETIME,
                    user_email VARCHAR(255) NOT NULL,
                    user_ip_address VARCHAR(45),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_credits_id) REFERENCES user_credits (id) ON DELETE CASCADE
                )
            """))
            print("✅ credit_purchases Tabelle erstellt")
            
            # 4. Erstelle Indizes für bessere Performance
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_credits_user_id ON user_credits (user_id)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_credit_events_user_credits_id ON credit_events (user_credits_id)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_credit_events_created_at ON credit_events (created_at)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_credit_purchases_user_credits_id ON credit_purchases (user_credits_id)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_credit_purchases_stripe_session_id ON credit_purchases (stripe_session_id)
            """))
            print("✅ Indizes erstellt")
            
    except Exception as e:
        print(f"❌ Fehler bei der Migration: {e}")
        raise
    finally:
        await engine.dispose()

async def verify_credit_system_tables():
    """Verifiziert die Credit-System Tabellen"""
    
    print("🔍 VERIFIKATION: Prüfe Credit-System Tabellen...")
    
    DATABASE_URL = "sqlite+aiosqlite:///./buildwise.db"
    
    try:
        engine = create_async_engine(DATABASE_URL, echo=False)
        
        async with engine.begin() as conn:
            # Prüfe user_credits Tabelle
            result = await conn.execute(text("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='table' AND name='user_credits'
            """))
            user_credits_exists = result.scalar()
            
            # Prüfe credit_events Tabelle
            result = await conn.execute(text("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='table' AND name='credit_events'
            """))
            credit_events_exists = result.scalar()
            
            # Prüfe credit_purchases Tabelle
            result = await conn.execute(text("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='table' AND name='credit_purchases'
            """))
            credit_purchases_exists = result.scalar()
            
            if user_credits_exists and credit_events_exists and credit_purchases_exists:
                print("✅ Alle Credit-System Tabellen existieren")
                
                # Zähle Einträge
                result = await conn.execute(text("SELECT COUNT(*) FROM user_credits"))
                user_credits_count = result.scalar()
                
                result = await conn.execute(text("SELECT COUNT(*) FROM credit_events"))
                credit_events_count = result.scalar()
                
                result = await conn.execute(text("SELECT COUNT(*) FROM credit_purchases"))
                credit_purchases_count = result.scalar()
                
                print(f"📊 Tabellen-Statistiken:")
                print(f"   - user_credits: {user_credits_count} Einträge")
                print(f"   - credit_events: {credit_events_count} Einträge")
                print(f"   - credit_purchases: {credit_purchases_count} Einträge")
                
            else:
                print("❌ Nicht alle Credit-System Tabellen existieren")
                print(f"   - user_credits: {'✅' if user_credits_exists else '❌'}")
                print(f"   - credit_events: {'✅' if credit_events_exists else '❌'}")
                print(f"   - credit_purchases: {'✅' if credit_purchases_exists else '❌'}")
                
    except Exception as e:
        print(f"❌ Fehler bei der Verifikation: {e}")
        raise
    finally:
        await engine.dispose()

async def create_initial_user_credits():
    """Erstellt UserCredits für bestehende Bauträger"""
    
    print("🔧 Erstelle UserCredits für bestehende Bauträger...")
    
    DATABASE_URL = "sqlite+aiosqlite:///./buildwise.db"
    
    try:
        engine = create_async_engine(DATABASE_URL, echo=False)
        
        async with engine.begin() as conn:
            # Finde alle Bauträger ohne UserCredits
            result = await conn.execute(text("""
                SELECT u.id, u.email, u.first_name, u.last_name
                FROM users u
                LEFT JOIN user_credits uc ON u.id = uc.user_id
                WHERE u.user_role = 'BAUTRAEGER' AND uc.id IS NULL
            """))
            
            bautraeger = result.fetchall()
            
            if not bautraeger:
                print("✅ Alle Bauträger haben bereits UserCredits")
                return
            
            print(f"📝 Erstelle UserCredits für {len(bautraeger)} Bauträger...")
            
            for user in bautraeger:
                user_id, email, first_name, last_name = user
                
                # Erstelle UserCredits mit Start-Credits
                await conn.execute(text("""
                    INSERT INTO user_credits (user_id, credits, plan_status, pro_start_date)
                    VALUES (?, 100, 'pro', CURRENT_TIMESTAMP)
                """), (user_id,))
                
                # Hole die erstellte UserCredits ID
                result = await conn.execute(text("""
                    SELECT id FROM user_credits WHERE user_id = ?
                """), (user_id,))
                user_credits_id = result.scalar()
                
                # Erstelle Registrierungs-Bonus Event
                await conn.execute(text("""
                    INSERT INTO credit_events (
                        user_credits_id, event_type, credits_change, 
                        credits_before, credits_after, description
                    )
                    VALUES (?, 'registration_bonus', 100, 0, 100, 'Willkommens-Bonus bei Registrierung')
                """), (user_credits_id,))
                
                print(f"   ✅ UserCredits für {email} ({first_name} {last_name}) erstellt")
            
            print(f"✅ UserCredits für {len(bautraeger)} Bauträger erstellt")
            
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der UserCredits: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Credit-System Migration")
    parser.add_argument("--action", choices=["migrate", "verify", "create-users"], 
                       default="migrate", help="Migration-Aktion")
    
    args = parser.parse_args()
    
    if args.action == "migrate":
        asyncio.run(create_credit_system_tables())
        print("✅ Migration abgeschlossen!")
    elif args.action == "verify":
        asyncio.run(verify_credit_system_tables())
        print("✅ Verifikation abgeschlossen!")
    elif args.action == "create-users":
        asyncio.run(create_initial_user_credits())
        print("✅ UserCredits für bestehende Bauträger erstellt!") 