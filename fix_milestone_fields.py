#!/usr/bin/env python3
"""
Fix milestone fields - Füge fehlende Felder zur milestones Tabelle hinzu
"""

import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

# Datenbankverbindung
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://buildwise:buildwise@localhost:5432/buildwise")

async def fix_milestone_fields():
    """Füge fehlende Felder zur milestones Tabelle hinzu"""
    
    engine = None
    try:
        # Erstelle Engine
        engine = create_async_engine(DATABASE_URL, echo=True)
        
        async with engine.begin() as conn:
            print("🔧 Füge fehlende Felder zur milestones Tabelle hinzu...")
            
            # Prüfe ob Felder bereits existieren
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'milestones' 
                AND column_name IN ('technical_specifications', 'quality_requirements', 'safety_requirements', 'environmental_requirements', 'category_specific_fields')
            """))
            
            existing_columns = [row[0] for row in result.fetchall()]
            print(f"📋 Bestehende Felder: {existing_columns}")
            
            # Füge fehlende Felder hinzu
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
                    await conn.execute(text(f"ALTER TABLE milestones ADD COLUMN {field_name} {field_type}"))
                else:
                    print(f"✅ Feld '{field_name}' existiert bereits")
            
            print("✅ Migration erfolgreich abgeschlossen!")
            
    except Exception as e:
        print(f"❌ Fehler bei der Migration: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if engine:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_milestone_fields()) 