#!/usr/bin/env python3
"""
Skript zur Erstellung von Test-BuildWise-Fees
"""

import asyncio
from datetime import datetime
from sqlalchemy import text
from app.core.database import engine

async def create_test_buildwise_fees():
    """Erstelle Test-BuildWise-Fees"""
    async with engine.begin() as conn:
        # Prüfe ob User mit ID 1 existiert
        user_result = await conn.execute(text("SELECT id FROM users WHERE id = 1"))
        user = user_result.fetchone()
        
        if not user:
            print("❌ User mit ID 1 nicht gefunden. Erstelle Test-User...")
            await conn.execute(text("""
                INSERT INTO users (id, email, hashed_password, first_name, last_name, user_type, is_active, created_at, updated_at)
                VALUES (1, 'test@buildwise.de', 'hashed_password', 'Test', 'User', 'bautraeger', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """))
        
        # Prüfe ob Projekt mit ID 1 existiert
        project_result = await conn.execute(text("SELECT id FROM projects WHERE id = 1"))
        project = project_result.fetchone()
        
        if not project:
            print("❌ Projekt mit ID 1 nicht gefunden. Erstelle Test-Projekt...")
            await conn.execute(text("""
                INSERT INTO projects (id, name, description, project_type, status, is_public, allow_quotes, created_at, updated_at)
                VALUES (1, 'Test Projekt', 'Ein Test-Projekt für BuildWise-Fees', 'residential', 'active', 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """))
        
        # Erstelle Test-BuildWise-Fees
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Test-Fee 1
        await conn.execute(text("""
            INSERT OR REPLACE INTO buildwise_fees (
                id, user_id, project_id, fee_month, fee_year, total_amount, 
                fee_percentage, status, created_at, updated_at
            ) VALUES (
                1, 1, 1, :month, :year, 150.00, 1.0, 'open', 
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
        """), {"month": current_month, "year": current_year})
        
        # Test-Fee 2 (vorheriger Monat)
        prev_month = current_month - 1 if current_month > 1 else 12
        prev_year = current_year if current_month > 1 else current_year - 1
        
        await conn.execute(text("""
            INSERT OR REPLACE INTO buildwise_fees (
                id, user_id, project_id, fee_month, fee_year, total_amount, 
                fee_percentage, status, created_at, updated_at
            ) VALUES (
                2, 1, 1, :month, :year, 250.00, 1.0, 'paid', 
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
        """), {"month": prev_month, "year": prev_year})
        
        # Test-Fee-Items
        await conn.execute(text("""
            INSERT OR REPLACE INTO buildwise_fee_items (
                id, buildwise_fee_id, quote_id, quote_amount, fee_amount, 
                fee_percentage, description, created_at
            ) VALUES (
                1, 1, 1, 15000.00, 150.00, 1.0, 
                'Test-Gebühr für akzeptiertes Angebot', CURRENT_TIMESTAMP
            )
        """))
        
        await conn.execute(text("""
            INSERT OR REPLACE INTO buildwise_fee_items (
                id, buildwise_fee_id, quote_id, quote_amount, fee_amount, 
                fee_percentage, description, created_at
            ) VALUES (
                2, 2, 2, 25000.00, 250.00, 1.0, 
                'Test-Gebühr für bezahltes Angebot', CURRENT_TIMESTAMP
            )
        """))
        
        print("✅ Test-BuildWise-Fees erfolgreich erstellt!")
        print(f"📊 Erstellt: 2 Gebühren für Monat {current_month}/{current_year} und {prev_month}/{prev_year}")

if __name__ == "__main__":
    asyncio.run(create_test_buildwise_fees()) 