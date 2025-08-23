#!/usr/bin/env python3
"""
Migration Script: Erweitere quotes-Tabelle um CostEstimateForm-Felder
Datum: 2024-12-19
Beschreibung: Führt die Migration aus, um alle fehlenden Felder zur quotes-Tabelle hinzuzufügen
"""

import asyncio
import sys
from sqlalchemy import text
from app.core.database import engine

async def run_migration():
    """Führt die Migration aus"""
    print("🚀 Starte Migration: Erweitere quotes-Tabelle...")
    
    # Felder die hinzugefügt werden sollen
    new_columns = {
        "quote_number": "VARCHAR(255)",
        "qualifications": "TEXT",
        "references": "TEXT", 
        "certifications": "TEXT",
        "technical_approach": "TEXT",
        "quality_standards": "TEXT",
        "safety_measures": "TEXT",
        "environmental_compliance": "TEXT",
        "risk_assessment": "TEXT",
        "contingency_plan": "TEXT",
        "additional_notes": "TEXT"
    }
    
    try:
        async with engine.begin() as conn:
            # Prüfe bestehende Spalten
            result = await conn.execute(text("PRAGMA table_info(quotes)"))
            existing_columns = {row[1] for row in result.fetchall()}
            print(f"📊 Bestehende Spalten: {len(existing_columns)}")
            
            # Füge nur fehlende Spalten hinzu
            added_count = 0
            for column_name, column_type in new_columns.items():
                if column_name not in existing_columns:
                    # Für reservierte Wörter wie 'references' Anführungszeichen verwenden
                    column_name_escaped = f'"{column_name}"' if column_name == 'references' else column_name
                    command = f"ALTER TABLE quotes ADD COLUMN {column_name_escaped} {column_type};"
                    print(f"📝 Füge Spalte hinzu: {column_name}")
                    await conn.execute(text(command))
                    added_count += 1
                    print(f"✅ Spalte '{column_name}' erfolgreich hinzugefügt")
                else:
                    print(f"⏭️ Spalte '{column_name}' existiert bereits")
        
        print(f"🎉 Migration erfolgreich abgeschlossen!")
        print(f"📊 {added_count} neue Spalten zur quotes-Tabelle hinzugefügt")
        if added_count > 0:
            print("✅ Hinzugefügte Spalten:")
            for column_name, column_type in new_columns.items():
                if column_name not in existing_columns:
                    print(f"   - {column_name} ({column_type})")
        else:
            print("ℹ️ Alle Spalten waren bereits vorhanden")
        
    except Exception as e:
        print(f"❌ Fehler bei der Migration: {e}")
        sys.exit(1)
    
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_migration())
