#!/usr/bin/env python3
"""
Script zur Hinzufügung der fehlenden Passwort-Reset-Felder
"""

import asyncio
import sys
import os
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from sqlalchemy import text


async def add_password_reset_fields():
    """Fügt die fehlenden Passwort-Reset-Felder zur Datenbank hinzu"""
    
    async for db in get_db():
        try:
            print("🔧 Füge Passwort-Reset-Felder zur Datenbank hinzu...")
            
            # SQL-Befehle zum Hinzufügen der Felder
            alter_queries = [
                "ALTER TABLE users ADD COLUMN password_reset_token VARCHAR",
                "ALTER TABLE users ADD COLUMN password_reset_sent_at DATETIME",
                "ALTER TABLE users ADD COLUMN password_reset_expires_at DATETIME"
            ]
            
            # Führe ALTER TABLE Befehle aus
            for i, query in enumerate(alter_queries):
                try:
                    result = await db.execute(text(query))
                    await db.commit()
                    print(f"✅ Feld {i+1} hinzugefügt")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print(f"ℹ️ Feld {i+1} existiert bereits")
                    else:
                        print(f"❌ Fehler beim Hinzufügen von Feld {i+1}: {e}")
            
            # Teste die Datenbank-Struktur
            print("\n🔍 Teste Datenbank-Struktur...")
            test_query = """
            SELECT id, email, password_reset_token, password_reset_sent_at, password_reset_expires_at 
            FROM users 
            WHERE email = 'admin@buildwise.de' 
            LIMIT 1
            """
            
            try:
                result = await db.execute(text(test_query))
                rows = result.fetchall()
                if rows:
                    print("✅ Datenbank-Struktur ist korrekt")
                    print(f"   Admin-User gefunden: {rows[0][1]}")
                else:
                    print("⚠️ Admin-User nicht gefunden")
            except Exception as e:
                print(f"❌ Fehler beim Testen: {e}")
            
            print("\n🎉 Passwort-Reset-Felder erfolgreich hinzugefügt!")
            
        except Exception as e:
            print(f"❌ Allgemeiner Fehler: {e}")
            await db.rollback()
        finally:
            await db.close()


if __name__ == "__main__":
    asyncio.run(add_password_reset_fields()) 