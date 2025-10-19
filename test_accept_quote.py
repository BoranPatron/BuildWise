#!/usr/bin/env python3
import asyncio
import sqlite3
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.quote_service import accept_quote

async def test_accept_quote():
    # Erstelle async engine
    engine = create_async_engine("sqlite+aiosqlite:///buildwise.db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            # Prüfe ob Quote 1 existiert
            conn = sqlite3.connect('buildwise.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, status, service_provider_id FROM quotes WHERE id = 1;')
            quote_info = cursor.fetchone()
            conn.close()
            
            if quote_info:
                print(f'Quote 1: Status={quote_info[1]}, Service Provider={quote_info[2]}')
                
                if quote_info[1] == 'ACCEPTED':
                    print('Quote ist bereits angenommen. Setze auf SUBMITTED zurück...')
                    conn = sqlite3.connect('buildwise.db')
                    cursor = conn.cursor()
                    cursor.execute("UPDATE quotes SET status = 'SUBMITTED' WHERE id = 1;")
                    conn.commit()
                    conn.close()
                
                # Akzeptiere das Angebot
                print('🔄 Akzeptiere Angebot...')
                result = await accept_quote(db, 1)
                
                if result:
                    print('✅ Angebot erfolgreich akzeptiert!')
                    print(f'Quote ID: {result.id}, Status: {result.status}')
                    
                    # Prüfe Benachrichtigungen
                    conn = sqlite3.connect('buildwise.db')
                    cursor = conn.cursor()
                    cursor.execute('SELECT id, recipient_id, type, title FROM notifications ORDER BY created_at DESC LIMIT 5;')
                    notifications = cursor.fetchall()
                    print('\n=== BENACHRICHTIGUNGEN ===')
                    for notif in notifications:
                        print(f'ID: {notif[0]}, Recipient: {notif[1]}, Type: {notif[2]}, Title: {notif[3]}')
                    conn.close()
                else:
                    print('❌ Fehler beim Akzeptieren des Angebots')
            else:
                print('❌ Quote 1 nicht gefunden')
                
        except Exception as e:
            print(f'❌ Fehler: {e}')
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_accept_quote())
