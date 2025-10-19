#!/usr/bin/env python3
"""
Migration: Füge Company Logo Felder zur users Tabelle hinzu
"""

import asyncio
import sys
import os

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from sqlalchemy import text

async def add_company_logo_fields():
    """Fügt Company Logo Felder zur users Tabelle hinzu."""
    
    print("[*] Migration: Company Logo Felder hinzufuegen")
    print("=" * 50)
    
    async with engine.begin() as conn:
        try:
            # 1. Füge company_logo Spalte hinzu
            print("[*] Fuege company_logo Spalte hinzu...")
            
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN company_logo VARCHAR(255)
            """))
            print("[OK] company_logo hinzugefuegt")
            
            # 2. Füge company_logo_advertising_consent Spalte hinzu
            print("[*] Fuege company_logo_advertising_consent Spalte hinzu...")
            
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN company_logo_advertising_consent BOOLEAN DEFAULT FALSE
            """))
            print("[OK] company_logo_advertising_consent hinzugefuegt")
            
            print("\n" + "=" * 50)
            print("[OK] Migration erfolgreich abgeschlossen!")
            print("=" * 50)
            
        except Exception as e:
            print(f"[ERROR] Fehler bei der Migration: {e}")
            raise

async def main():
    """Hauptfunktion"""
    try:
        await add_company_logo_fields()
    except Exception as e:
        print(f"\n[ERROR] Migration fehlgeschlagen: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

