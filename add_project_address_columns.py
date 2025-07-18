#!/usr/bin/env python3
"""
Fügt Adressspalten zur Projekte-Tabelle hinzu (SQLite)
"""

import asyncio
import sys
import os

# Pfad zum app-Verzeichnis hinzufügen
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import get_db
from sqlalchemy import text

async def add_project_address_columns():
    """Fügt Adressspalten zur Projekte-Tabelle hinzu"""
    
    print("🔧 Füge Adressspalten zur Projekte-Tabelle hinzu (SQLite)")
    print("=" * 50)
    
    async for db in get_db():
        try:
            # Überprüfe zuerst, welche Spalten bereits existieren (SQLite)
            result = await db.execute(text("PRAGMA table_info(projects)"))
            existing_columns = [row[1] for row in result.fetchall()]
            print(f"📋 Bestehende Spalten: {existing_columns}")
            
            # Definiere die neuen Spalten
            new_columns = [
                ("address", "TEXT"),
                ("address_street", "TEXT"),
                ("address_zip", "TEXT"),
                ("address_city", "TEXT"),
                ("address_country", "TEXT"),
                ("address_latitude", "REAL"),
                ("address_longitude", "REAL"),
                ("address_geocoded", "INTEGER"),
                ("address_geocoding_date", "TEXT")
            ]
            
            # Füge fehlende Spalten hinzu
            for column_name, column_type in new_columns:
                if column_name not in existing_columns:
                    print(f"➕ Füge Spalte hinzu: {column_name}")
                    
                    if column_type == "INTEGER":
                        sql = f"ALTER TABLE projects ADD COLUMN {column_name} INTEGER DEFAULT 0"
                    else:
                        sql = f"ALTER TABLE projects ADD COLUMN {column_name} {column_type}"
                    
                    await db.execute(text(sql))
                    print(f"   ✅ Spalte {column_name} hinzugefügt")
                else:
                    print(f"   ℹ️ Spalte {column_name} existiert bereits")
            
            await db.commit()
            print("✅ Alle Adressspalten erfolgreich hinzugefügt")
            
            # Überprüfe das finale Schema
            result = await db.execute(text("PRAGMA table_info(projects)"))
            all_columns = result.fetchall()
            address_columns = [col for col in all_columns if 'address' in col[1].lower()]
            
            print(f"📋 Address-Spalten nach Update:")
            for col in address_columns:
                print(f"   {col[1]}: {col[2]} (nullable: {col[3]})")
            
            break
            
        except Exception as e:
            print(f"❌ Fehler: {str(e)}")
            await db.rollback()
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(add_project_address_columns()) 