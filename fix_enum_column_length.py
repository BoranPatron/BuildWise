#!/usr/bin/env python3
"""
Fix: Erweitere user_role VARCHAR Spalte
"""

import asyncio
import sys
import os

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from sqlalchemy import text

async def fix_enum_column_length():
    """Erweitert die user_role Spalte für längere Enum-Werte."""
    
    print("🔧 Fix: Erweitere user_role VARCHAR Spalte")
    print("=" * 50)
    
    async with engine.begin() as conn:
        try:
            # Prüfe aktuelle Spalten-Definition
            print("📊 Aktuelle Spalten-Definition:")
            result = await conn.execute(text("PRAGMA table_info(users);"))
            
            for row in result:
                if 'user_role' in str(row):
                    print(f"   Vorher: {row}")
            
            # SQLite kann Spalten nicht direkt ändern - wir müssen eine neue Tabelle erstellen
            print("\n🔄 Erstelle temporäre Tabelle mit erweiterter Spalte...")
            
            # 1. Erstelle Backup der aktuellen Daten
            await conn.execute(text("""
                CREATE TABLE users_backup AS 
                SELECT * FROM users
            """))
            print("✅ Backup erstellt")
            
            # 2. Lösche alte Tabelle (nur die Struktur)
            await conn.execute(text("DROP TABLE users"))
            print("✅ Alte Tabelle gelöscht")
            
            # 3. Erstelle neue Tabelle mit erweiterter user_role Spalte
            await conn.execute(text("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255),
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    phone VARCHAR(20),
                    user_type VARCHAR(20) DEFAULT 'PRIVATE',
                    company_name VARCHAR(255),
                    company_address TEXT,
                    company_phone VARCHAR(20),
                    company_website VARCHAR(255),
                    business_license VARCHAR(255),
                    bio TEXT,
                    profile_image VARCHAR(255),
                    region VARCHAR(100),
                    languages VARCHAR(255),
                    language_preference VARCHAR(10) DEFAULT 'de',
                    is_active BOOLEAN DEFAULT 1,
                    is_verified BOOLEAN DEFAULT 0,
                    auth_provider VARCHAR(20) DEFAULT 'email',
                    google_id VARCHAR(255),
                    microsoft_id VARCHAR(255),
                    last_login_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_role VARCHAR(50),
                    role_selected BOOLEAN DEFAULT 0,
                    role_selected_at DATETIME,
                    subscription_plan VARCHAR(20) DEFAULT 'basis',
                    subscription_status VARCHAR(20) DEFAULT 'inactive',
                    subscription_id VARCHAR(255),
                    customer_id VARCHAR(255),
                    subscription_start DATETIME,
                    subscription_end DATETIME,
                    max_gewerke INTEGER DEFAULT 3,
                    consents JSON
                )
            """))
            print("✅ Neue Tabelle mit VARCHAR(50) für user_role erstellt")
            
            # 4. Kopiere Daten zurück
            await conn.execute(text("""
                INSERT INTO users SELECT * FROM users_backup
            """))
            print("✅ Daten zurückkopiert")
            
            # 5. Lösche Backup
            await conn.execute(text("DROP TABLE users_backup"))
            print("✅ Backup gelöscht")
            
            # 6. Prüfe neue Spalten-Definition
            print("\n📊 Neue Spalten-Definition:")
            result = await conn.execute(text("PRAGMA table_info(users);"))
            
            for row in result:
                if 'user_role' in str(row):
                    print(f"   Nachher: {row}")
            
            # 7. Prüfe Daten
            print("\n📋 Daten nach Migration:")
            result = await conn.execute(text("""
                SELECT id, email, user_role, LENGTH(user_role) as role_length
                FROM users 
                WHERE user_role IS NOT NULL
                ORDER BY id
            """))
            
            for row in result:
                user_id, email, role, length = row
                print(f"   ID {user_id}: {email} -> '{role}' (Länge: {length})")
            
            print("\n✅ user_role Spalte erfolgreich erweitert!")
            
        except Exception as e:
            print(f"❌ Fehler bei der Spalten-Erweiterung: {e}")
            # Versuche Rollback
            try:
                await conn.execute(text("DROP TABLE IF EXISTS users"))
                await conn.execute(text("ALTER TABLE users_backup RENAME TO users"))
                print("🔄 Rollback durchgeführt")
            except:
                pass
            raise

if __name__ == "__main__":
    asyncio.run(fix_enum_column_length()) 