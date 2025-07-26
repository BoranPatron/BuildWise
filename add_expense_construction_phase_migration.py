#!/usr/bin/env python3
"""
Migration: Fügt construction_phase Feld zur Expense-Tabelle hinzu
Datum: 2025-01-27
Beschreibung: Erweitert die Expense-Tabelle um ein construction_phase Feld für Analytics
"""

import asyncio
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

async def add_expense_construction_phase():
    """Fügt construction_phase Feld zur Expense-Tabelle hinzu"""
    
    print("🚀 MIGRATION: Füge construction_phase Feld zur Expense-Tabelle hinzu...")
    
    # Verwende SQLite für die Entwicklung
    DATABASE_URL = "sqlite+aiosqlite:///./buildwise.db"
    
    try:
        # Erstelle Engine
        engine = create_async_engine(DATABASE_URL, echo=False)
        
        async with engine.begin() as conn:
            # Prüfe ob das Feld bereits existiert
            result = await conn.execute(text("""
                SELECT COUNT(*) FROM pragma_table_info('expenses') 
                WHERE name = 'construction_phase'
            """))
            field_exists = result.scalar()
            
            if field_exists:
                print("✅ construction_phase Feld existiert bereits")
                return
            
            # Füge das Feld hinzu
            await conn.execute(text("""
                ALTER TABLE expenses 
                ADD COLUMN construction_phase VARCHAR(100)
            """))
            
            print("✅ construction_phase Feld erfolgreich hinzugefügt")
            
            # Aktualisiere bestehende Ausgaben mit der aktuellen Bauphase des Projekts
            await conn.execute(text("""
                UPDATE expenses 
                SET construction_phase = (
                    SELECT construction_phase 
                    FROM projects 
                    WHERE projects.id = expenses.project_id
                )
                WHERE construction_phase IS NULL
            """))
            
            print("✅ Bestehende Ausgaben mit Projekt-Bauphasen aktualisiert")
            
    except Exception as e:
        print(f"❌ Fehler bei der Migration: {e}")
        raise
    finally:
        await engine.dispose()

async def rollback_expense_construction_phase():
    """Rollback: Entfernt construction_phase Feld aus der Expense-Tabelle"""
    
    print("🔄 ROLLBACK: Entferne construction_phase Feld aus der Expense-Tabelle...")
    
    DATABASE_URL = "sqlite+aiosqlite:///./buildwise.db"
    
    try:
        engine = create_async_engine(DATABASE_URL, echo=False)
        
        async with engine.begin() as conn:
            # Prüfe ob das Feld existiert
            result = await conn.execute(text("""
                SELECT COUNT(*) FROM pragma_table_info('expenses') 
                WHERE name = 'construction_phase'
            """))
            field_exists = result.scalar()
            
            if not field_exists:
                print("✅ construction_phase Feld existiert nicht")
                return
            
            # SQLite unterstützt kein DROP COLUMN - wir müssen eine neue Tabelle erstellen
            print("⚠️  SQLite unterstützt kein DROP COLUMN. Manuelle Entfernung erforderlich.")
            print("💡 Verwenden Sie ein SQLite-Tool wie DB Browser for SQLite")
            
    except Exception as e:
        print(f"❌ Fehler beim Rollback: {e}")
        raise
    finally:
        await engine.dispose()

async def verify_expense_construction_phase():
    """Verifiziert die Migration"""
    
    print("🔍 VERIFIKATION: Prüfe construction_phase Feld...")
    
    DATABASE_URL = "sqlite+aiosqlite:///./buildwise.db"
    
    try:
        engine = create_async_engine(DATABASE_URL, echo=False)
        
        async with engine.begin() as conn:
            # Prüfe ob das Feld existiert
            result = await conn.execute(text("""
                SELECT COUNT(*) FROM pragma_table_info('expenses') 
                WHERE name = 'construction_phase'
            """))
            field_exists = result.scalar()
            
            if field_exists:
                print("✅ construction_phase Feld existiert")
                
                # Zähle Ausgaben mit Bauphasen
                result = await conn.execute(text("""
                    SELECT COUNT(*) FROM expenses WHERE construction_phase IS NOT NULL
                """))
                expenses_with_phase = result.scalar()
                
                result = await conn.execute(text("""
                    SELECT COUNT(*) FROM expenses
                """))
                total_expenses = result.scalar()
                
                print(f"📊 Ausgaben mit Bauphasen: {expenses_with_phase}/{total_expenses}")
                
            else:
                print("❌ construction_phase Feld existiert nicht")
                
    except Exception as e:
        print(f"❌ Fehler bei der Verifikation: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Expense construction_phase Migration")
    parser.add_argument("--action", choices=["migrate", "rollback", "verify"], 
                       default="migrate", help="Migration-Aktion")
    
    args = parser.parse_args()
    
    if args.action == "migrate":
        asyncio.run(add_expense_construction_phase())
    elif args.action == "rollback":
        asyncio.run(rollback_expense_construction_phase())
    elif args.action == "verify":
        asyncio.run(verify_expense_construction_phase())
    
    print("✅ Migration abgeschlossen!") 