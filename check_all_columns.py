#!/usr/bin/env python3
"""
Detaillierte Überprüfung aller Spalten in der quotes-Tabelle
"""

import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check_all_columns():
    """Zeigt alle Spalten der quotes-Tabelle an"""
    print("🔍 Detaillierte Analyse der quotes-Tabelle...")
    
    try:
        async with engine.begin() as conn:
            # Hole alle Spalten-Informationen
            result = await conn.execute(text("PRAGMA table_info(quotes)"))
            columns = result.fetchall()
            
            print(f"📊 Gesamt-Spalten: {len(columns)}")
            print("\n📋 Alle Spalten der quotes-Tabelle:")
            print("ID | Name | Typ | NotNull | Default | PrimaryKey")
            print("-" * 60)
            
            # Zeige alle Spalten mit Details
            for col in columns:
                col_id, name, type_name, not_null, default, pk = col
                nullable = "NOT NULL" if not_null else "NULL"
                primary = "PK" if pk else ""
                default_val = f"({default})" if default else ""
                print(f"{col_id:2} | {name:25} | {type_name:12} | {nullable:8} | {default_val:10} | {primary}")
            
            # Prüfe speziell die neuen Felder
            print(f"\n🆕 Neue Felder (sollten alle vorhanden sein):")
            new_fields = [
                "quote_number", "qualifications", "references", "certifications",
                "technical_approach", "quality_standards", "safety_measures", 
                "environmental_compliance", "risk_assessment", "contingency_plan", 
                "additional_notes"
            ]
            
            existing_names = [col[1] for col in columns]
            for field in new_fields:
                status = "✅" if field in existing_names else "❌"
                print(f"{status} {field}")
            
            # Teste eine Abfrage mit den neuen Feldern
            print(f"\n🧪 Test-Abfrage mit neuen Feldern:")
            try:
                test_query = """
                SELECT id, quote_number, qualifications, technical_approach, additional_notes 
                FROM quotes 
                LIMIT 1
                """
                test_result = await conn.execute(text(test_query))
                row = test_result.fetchone()
                if row:
                    print(f"✅ Abfrage erfolgreich - ID: {row[0]}")
                    print(f"   quote_number: {row[1]}")
                    print(f"   qualifications: {row[2]}")
                    print(f"   technical_approach: {row[3]}")
                    print(f"   additional_notes: {row[4]}")
                else:
                    print("ℹ️ Keine Daten in der Tabelle")
            except Exception as e:
                print(f"❌ Fehler bei Test-Abfrage: {e}")
                
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    asyncio.run(check_all_columns())
