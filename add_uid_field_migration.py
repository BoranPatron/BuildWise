"""
Migration: UID-Feld zu Firmeninformationen hinzufügen
"""

import asyncio
from sqlalchemy import text
from app.core.database import engine

async def add_uid_field():
    """Fügt das UID-Feld zur users-Tabelle hinzu"""
    
    async with engine.begin() as conn:
        # Prüfe ob die Spalte bereits existiert
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM pragma_table_info('users') 
            WHERE name = 'company_uid'
        """))
        
        if result.scalar() == 0:
            # Füge die UID-Spalte hinzu
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN company_uid VARCHAR(50) NULL
            """))
            print("✅ UID-Feld zur users-Tabelle hinzugefügt")
        else:
            print("ℹ️  UID-Feld existiert bereits")

if __name__ == "__main__":
    asyncio.run(add_uid_field())
