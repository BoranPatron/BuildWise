#!/usr/bin/env python3
"""
Pruefe fehlende Spalten in der quotes-Tabelle
"""

import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check_missing_columns():
    """Prueft fehlende Spalten"""
    print("Pruefe quotes-Tabelle...")
    
    # Erwartete neue Spalten
    expected_columns = [
        "quote_number", "qualifications", "references", "certifications",
        "technical_approach", "quality_standards", "safety_measures", 
        "environmental_compliance", "risk_assessment", "contingency_plan", 
        "additional_notes"
    ]
    
    try:
        async with engine.begin() as conn:
            # Hole alle Spalten
            result = await conn.execute(text("PRAGMA table_info(quotes)"))
            columns = result.fetchall()
            
            existing_names = [col[1] for col in columns]
            print(f"Gesamt Spalten: {len(columns)}")
            
            print("\nStatus der erwarteten Spalten:")
            missing = []
            for col in expected_columns:
                if col in existing_names:
                    print(f"OK: {col}")
                else:
                    print(f"FEHLT: {col}")
                    missing.append(col)
            
            if missing:
                print(f"\nFehlende Spalten: {missing}")
                
                # Fuege fehlende Spalten hinzu
                print("Fuege fehlende Spalten hinzu...")
                for col in missing:
                    if col == 'references':
                        # Verwende Anfuehrungszeichen fuer reserviertes Wort
                        cmd = f'ALTER TABLE quotes ADD COLUMN "references" TEXT;'
                    else:
                        cmd = f'ALTER TABLE quotes ADD COLUMN {col} TEXT;'
                    
                    print(f"Fuehre aus: {cmd}")
                    await conn.execute(text(cmd))
                    print(f"Spalte {col} hinzugefuegt")
                
                print("Alle fehlenden Spalten hinzugefuegt!")
            else:
                print("Alle Spalten sind vorhanden!")
                
    except Exception as e:
        print(f"Fehler: {e}")

if __name__ == "__main__":
    asyncio.run(check_missing_columns())
