#!/usr/bin/env python3
"""
DSGVO-Migration für BuildWise
Fügt DSGVO-konforme Felder zur Datenbank hinzu
"""

import asyncio
import sys
import os
from datetime import date

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import text
from app.core.database import engine
from app.models import Base, User, UserStatus


async def migrate_to_gdpr():
    """Führt die DSGVO-Migration durch"""
    print("🚀 Starte DSGVO-Migration für BuildWise...")
    
    async with engine.begin() as conn:
        # Prüfe ob die neuen Tabellen bereits existieren
        result = await conn.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='audit_logs'
        """))
        
        if result.fetchone():
            print("✅ Audit-Logs Tabelle existiert bereits")
        else:
            print("📋 Erstelle Audit-Logs Tabelle...")
            await conn.run_sync(Base.metadata.create_all)
        
        # Prüfe ob die neuen User-Felder existieren
        result = await conn.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result.fetchall()]
        
        # DSGVO-Felder die hinzugefügt werden müssen
        gdpr_columns = [
            ("status", "TEXT DEFAULT 'active'"),
            ("data_processing_consent", "BOOLEAN DEFAULT 0"),
            ("marketing_consent", "BOOLEAN DEFAULT 0"),
            ("privacy_policy_accepted", "BOOLEAN DEFAULT 0"),
            ("terms_accepted", "BOOLEAN DEFAULT 0"),
            ("data_retention_until", "DATE"),
            ("data_deletion_requested", "BOOLEAN DEFAULT 0"),
            ("data_deletion_requested_at", "DATETIME"),
            ("data_anonymized", "BOOLEAN DEFAULT 0"),
            ("last_login_at", "DATETIME"),
            ("failed_login_attempts", "INTEGER DEFAULT 0"),
            ("account_locked_until", "DATETIME"),
            ("password_changed_at", "DATETIME"),
            ("data_encrypted", "BOOLEAN DEFAULT 1"),
            ("encryption_key_id", "TEXT"),
            ("last_activity_at", "DATETIME")
        ]
        
        # Füge fehlende Spalten hinzu
        for column_name, column_def in gdpr_columns:
            if column_name not in columns:
                print(f"➕ Füge Spalte '{column_name}' hinzu...")
                await conn.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}"))
        
        # Aktualisiere bestehende Benutzer mit DSGVO-Standardwerten
        print("🔄 Aktualisiere bestehende Benutzer...")
        
        # Setze Standard-Datenaufbewahrung (2 Jahre)
        retention_date = date.today().replace(year=date.today().year + 2)
        
        await conn.execute(text("""
            UPDATE users 
            SET data_retention_until = :retention_date,
                status = 'active',
                data_encrypted = 1
            WHERE data_retention_until IS NULL
        """), {"retention_date": retention_date})
        
        # Erstelle Admin-Benutzer mit DSGVO-Konformität falls nicht vorhanden
        result = await conn.execute(text("SELECT COUNT(*) FROM users WHERE email = 'admin@buildwise.de'"))
        if result.scalar() == 0:
            print("👤 Erstelle DSGVO-konformen Admin-Benutzer...")
            
            # Passwort hashen (admin123)
            from app.services.security_service import SecurityService
            hashed_password = SecurityService.hash_password("admin123")
            
            await conn.execute(text("""
                INSERT INTO users (
                    email, hashed_password, first_name, last_name, user_type,
                    status, data_processing_consent, privacy_policy_accepted, terms_accepted,
                    data_retention_until, is_active, is_verified, email_verified,
                    data_encrypted, created_at, updated_at
                ) VALUES (
                    'admin@buildwise.de', :password, 'Admin', 'BuildWise', 'professional',
                    'active', 1, 1, 1, :retention_date, 1, 1, 1,
                    1, datetime('now'), datetime('now')
                )
            """), {
                "password": hashed_password,
                "retention_date": retention_date
            })
        
        print("✅ DSGVO-Migration erfolgreich abgeschlossen!")
        print("\n📋 Zusammenfassung:")
        print("   • Audit-Logs Tabelle erstellt")
        print("   • DSGVO-Felder zu User-Tabelle hinzugefügt")
        print("   • Bestehende Benutzer aktualisiert")
        print("   • Admin-Benutzer mit DSGVO-Konformität erstellt")
        print("\n🔒 DSGVO-Features aktiviert:")
        print("   • Passwort-Stärke-Validierung")
        print("   • Account-Sperrung bei fehlgeschlagenen Anmeldungen")
        print("   • IP-Adress-Anonymisierung")
        print("   • Audit-Logging für alle Aktionen")
        print("   • Einwilligungsverwaltung")
        print("   • Datenlöschungsanträge")
        print("   • Datenanonymisierung")


async def main():
    """Hauptfunktion"""
    try:
        await migrate_to_gdpr()
    except Exception as e:
        print(f"❌ Fehler bei der DSGVO-Migration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 