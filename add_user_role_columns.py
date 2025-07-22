#!/usr/bin/env python3
"""
Migration: Füge User-Rollen-Felder hinzu
"""

import asyncio
import sys
import os
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from sqlalchemy import text

async def add_user_role_columns():
    """Fügt die neuen Rollen-Felder zur users Tabelle hinzu."""
    
    print("🚀 Füge User-Rollen-Felder hinzu...")
    print("=" * 60)
    
    async with engine.begin() as conn:
        try:
            # Für SQLite: Prüfe ob Spalten bereits existieren
            result = await conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result]
            
            # Füge user_role hinzu
            if 'user_role' not in columns:
                await conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN user_role VARCHAR(20)
                """))
                print("✅ Spalte 'user_role' hinzugefügt")
            else:
                print("ℹ️ Spalte 'user_role' existiert bereits")
            
            # Füge role_selected hinzu
            if 'role_selected' not in columns:
                await conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN role_selected BOOLEAN DEFAULT FALSE
                """))
                print("✅ Spalte 'role_selected' hinzugefügt")
            else:
                print("ℹ️ Spalte 'role_selected' existiert bereits")
            
            # Füge role_selected_at hinzu
            if 'role_selected_at' not in columns:
                await conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN role_selected_at TIMESTAMP
                """))
                print("✅ Spalte 'role_selected_at' hinzugefügt")
            else:
                print("ℹ️ Spalte 'role_selected_at' existiert bereits")
            
            # Erstelle Index für Performance
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_role 
                ON users(user_role)
            """))
            print("✅ Index 'idx_users_role' erstellt")
            
            # Setze Admin-Rolle für bestehende Admin-Benutzer
            await conn.execute(text("""
                UPDATE users 
                SET user_role = 'admin', 
                    role_selected = 1,
                    role_selected_at = datetime('now')
                WHERE email LIKE '%admin%' 
                AND user_role IS NULL
            """))
            print("✅ Admin-Rollen aktualisiert")
            
            # Setze Dienstleister-Rolle für bestehende Dienstleister
            await conn.execute(text("""
                UPDATE users 
                SET user_role = 'dienstleister', 
                    role_selected = 1,
                    role_selected_at = datetime('now')
                WHERE user_type = 'service_provider' 
                AND user_role IS NULL
            """))
            print("✅ Dienstleister-Rollen aktualisiert")
            
            print("\n✅ Migration erfolgreich abgeschlossen!")
            
        except Exception as e:
            print(f"❌ Fehler bei der Migration: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(add_user_role_columns()) 