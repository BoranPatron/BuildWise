#!/usr/bin/env python3
"""
Direkte Datenbank-Reparatur - Füge fehlende Felder hinzu
"""

import asyncio
import os
import asyncpg
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

# Datenbankverbindung
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://buildwise:buildwise@localhost:5432/buildwise")

async def fix_database():
    """Repariere die Datenbank direkt"""
    
    conn = None
    try:
        # Verbinde zur Datenbank
        print("🔧 Verbinde zur Datenbank...")
        conn = await asyncpg.connect(DATABASE_URL)
        
        print("🔧 Prüfe milestones Tabelle...")
        
        # Prüfe ob Felder existieren
        columns_result = await conn.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'milestones' 
            AND column_name IN (
                'technical_specifications', 
                'quality_requirements', 
                'safety_requirements', 
                'environmental_requirements', 
                'category_specific_fields'
            )
        """)
        
        existing_columns = [row['column_name'] for row in columns_result]
        print(f"📋 Bestehende Felder: {existing_columns}")
        
        # Felder die hinzugefügt werden müssen
        fields_to_add = [
            ("technical_specifications", "TEXT"),
            ("quality_requirements", "TEXT"),
            ("safety_requirements", "TEXT"),
            ("environmental_requirements", "TEXT"),
            ("category_specific_fields", "TEXT")
        ]
        
        for field_name, field_type in fields_to_add:
            if field_name not in existing_columns:
                print(f"➕ Füge Feld '{field_name}' hinzu...")
                await conn.execute(f"ALTER TABLE milestones ADD COLUMN {field_name} {field_type}")
                print(f"✅ Feld '{field_name}' hinzugefügt")
            else:
                print(f"✅ Feld '{field_name}' existiert bereits")
        
        print("✅ Datenbank-Reparatur erfolgreich abgeschlossen!")
        
        # Prüfe die Tabelle nochmal
        final_check = await conn.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'milestones' 
            ORDER BY column_name
        """)
        
        print("📋 Alle Felder in milestones Tabelle:")
        for row in final_check:
            print(f"  - {row['column_name']}")
        
    except Exception as e:
        print(f"❌ Fehler bei der Datenbank-Reparatur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_database()) 