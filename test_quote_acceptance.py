#!/usr/bin/env python3
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.quote_service import accept_quote
from app.core.database import get_db
import sqlite3

async def test_quote_acceptance():
    # Erstelle eine neue Quote zum Testen
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    # Lösche alte Test-Benachrichtigungen
    cursor.execute("DELETE FROM notifications WHERE type = 'quote_accepted'")
    
    # Erstelle eine neue Test-Quote
    cursor.execute("""
    INSERT OR REPLACE INTO quotes (
        id, service_provider_id, milestone_id, project_id, 
        status, total_amount, currency, title, created_at
    ) VALUES (
        999, 77, 1, 1, 
        'SUBMITTED', 15000.0, 'CHF', 'Test Quote', datetime('now')
    )
    """)
    conn.commit()
    conn.close()
    
    print("✅ Test-Quote erstellt (ID: 999)")
    
    # Teste Quote-Annahme über die Service-Funktion
    try:
        # Erstelle async DB Session
        engine = create_async_engine("sqlite+aiosqlite:///buildwise.db")
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as db:
            result = await accept_quote(db, 999)
            if result:
                print("✅ Quote erfolgreich angenommen")
                print(f"   Status: {result.status}")
            else:
                print("❌ Quote nicht gefunden")
                
    except Exception as e:
        print(f"❌ Fehler beim Testen der Quote-Annahme: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_quote_acceptance())