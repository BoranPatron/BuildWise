#!/usr/bin/env python3
"""
Verifikations-Skript: Überprüfe die quotes-Tabelle nach der Migration
"""

import asyncio
from sqlalchemy import text
from app.core.database import engine

async def verify_migration():
    """Überprüft die Migration"""
    print("🔍 Überprüfe quotes-Tabelle nach Migration...")
    
    expected_columns = [
        "quote_number", "qualifications", "references", "certifications",
        "technical_approach", "quality_standards", "safety_measures", 
        "environmental_compliance", "risk_assessment", "contingency_plan", 
        "additional_notes"
    ]
    
    try:
        async with engine.begin() as conn:
            # Hole alle Spalten-Informationen
            result = await conn.execute(text("PRAGMA table_info(quotes)"))
            columns = result.fetchall()
            
            print(f"📊 Gesamt-Spalten in quotes-Tabelle: {len(columns)}")
            print("\n🔍 Überprüfung der neuen Spalten:")
            
            existing_column_names = [col[1] for col in columns]
            
            all_present = True
            for expected_col in expected_columns:
                if expected_col in existing_column_names:
                    print(f"✅ {expected_col} - vorhanden")
                else:
                    print(f"❌ {expected_col} - FEHLT!")
                    all_present = False
            
            if all_present:
                print("\n🎉 Migration erfolgreich! Alle erwarteten Spalten sind vorhanden.")
                
                # Teste eine einfache Abfrage
                test_result = await conn.execute(text("SELECT COUNT(*) FROM quotes"))
                count = test_result.scalar()
                print(f"📈 Anzahl vorhandener Angebote: {count}")
                
                # Zeige die vollständige Tabellenstruktur
                print(f"\n📋 Vollständige Tabellenstruktur:")
                for col in columns:
                    col_id, name, type_name, not_null, default, pk = col
                    nullable = "NOT NULL" if not_null else "NULL"
                    primary = "PRIMARY KEY" if pk else ""
                    print(f"   {name} ({type_name}) {nullable} {primary}".strip())
                    
            else:
                print("\n❌ Migration unvollständig! Einige Spalten fehlen.")
                
    except Exception as e:
        print(f"❌ Fehler bei der Verifikation: {e}")

if __name__ == "__main__":
    asyncio.run(verify_migration())
