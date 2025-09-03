#!/usr/bin/env python3
"""
Direkte SQL-Abfrage der quotes-Tabelle
"""

import asyncio
from sqlalchemy import text
from app.core.database import engine

async def direct_sql_check():
    """Direkte SQL-Abfrage"""
    print("Direkte SQL-Abfrage der quotes-Tabelle...")
    
    try:
        async with engine.begin() as conn:
            # Zeige alle Spalten-Namen
            result = await conn.execute(text("PRAGMA table_info(quotes)"))
            columns = result.fetchall()
            
            print("Alle Spalten-Namen:")
            for i, col in enumerate(columns):
                print(f"{i+1:2d}. {col[1]}")
            
            # Pruefe ob wir eine Abfrage mit den neuen Feldern machen koennen
            print("\nTeste SELECT mit neuen Feldern...")
            try:
                query = """
                SELECT 
                    id,
                    quote_number,
                    qualifications,
                    "references",
                    certifications,
                    technical_approach,
                    quality_standards,
                    safety_measures,
                    environmental_compliance,
                    risk_assessment,
                    contingency_plan,
                    additional_notes
                FROM quotes 
                LIMIT 1
                """
                result = await conn.execute(text(query))
                row = result.fetchone()
                
                if row:
                    print("SELECT erfolgreich! Daten:")
                    print(f"ID: {row[0]}")
                    print(f"quote_number: {row[1]}")
                    print(f"qualifications: {row[2]}")
                    print(f"references: {row[3]}")
                    print(f"certifications: {row[4]}")
                else:
                    print("SELECT erfolgreich, aber keine Daten vorhanden")
                    
            except Exception as e:
                print(f"SELECT fehlgeschlagen: {e}")
                
            # Zeige CREATE TABLE Statement
            print("\nCREATE TABLE Statement:")
            result = await conn.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='quotes'"))
            create_sql = result.scalar()
            if create_sql:
                # Zeige nur die letzten Zeilen (neue Spalten)
                lines = create_sql.split('\n')
                print("Letzte 15 Zeilen des CREATE TABLE:")
                for line in lines[-15:]:
                    print(line)
                    
    except Exception as e:
        print(f"Fehler: {e}")

if __name__ == "__main__":
    asyncio.run(direct_sql_check())
