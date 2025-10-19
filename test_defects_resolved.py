#!/usr/bin/env python3
import asyncio
import sqlite3
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.api.acceptance import complete_final_acceptance
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User

async def test_defects_resolved():
    # Erstelle async engine
    engine = create_async_engine("sqlite+aiosqlite:///buildwise.db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            # Prüfe bestehende Abnahmen
            conn = sqlite3.connect('buildwise.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, milestone_id, service_provider_id, status FROM acceptances LIMIT 5;')
            acceptances = cursor.fetchall()
            print('=== BESTEHENDE ABNAHMEN ===')
            for acc in acceptances:
                print(f'ID: {acc[0]}, Milestone: {acc[1]}, Service Provider: {acc[2]}, Status: {acc[3]}')
            
            # Prüfe User 77 (Dienstleister)
            cursor.execute('SELECT id, first_name, last_name, user_role FROM users WHERE id = 77;')
            user_info = cursor.fetchall()
            print(f'\n=== USER 77 ===')
            for user in user_info:
                print(f'ID: {user[0]}, Name: {user[1]} {user[2]}, Role: {user[3]}')
            
            conn.close()
            
            if acceptances:
                acceptance_id = acceptances[0][0]  # Erste Abnahme verwenden
                print(f'\n🔄 Teste Mängelbehebung für Acceptance {acceptance_id}...')
                
                # Simuliere Dienstleister User 77
                from sqlalchemy import select
                user_stmt = select(User).where(User.id == 77)
                user_result = await db.execute(user_stmt)
                current_user = user_result.scalar_one_or_none()
                
                if current_user:
                    print(f'✅ User gefunden: {current_user.first_name} {current_user.last_name} ({current_user.user_role})')
                    
                    # Teste complete_final_acceptance direkt
                    completion_data = {
                        'accepted': True,
                        'milestone_id': acceptances[0][1]  # Milestone ID
                    }
                    
                    # Simuliere den API-Call (vereinfacht)
                    from app.api.acceptance import complete_final_acceptance
                    # Da wir die Funktion direkt aufrufen, müssen wir die Dependencies manuell setzen
                    print('⚠️ Für vollständigen Test muss die API über HTTP aufgerufen werden')
                    print(f'   POST /api/v1/acceptance/{acceptance_id}/final-complete')
                    print(f'   Body: {completion_data}')
                    print(f'   Als User: {current_user.id} ({current_user.user_role})')
                    
                else:
                    print('❌ User 77 nicht gefunden')
            else:
                print('❌ Keine Abnahmen gefunden')
                
            # Prüfe bestehende Benachrichtigungen
            conn = sqlite3.connect('buildwise.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, recipient_id, type, title, created_at FROM notifications ORDER BY created_at DESC LIMIT 5;')
            notifications = cursor.fetchall()
            print('\n=== AKTUELLE BENACHRICHTIGUNGEN ===')
            for notif in notifications:
                print(f'ID: {notif[0]}, Recipient: {notif[1]}, Type: {notif[2]}, Title: {notif[3]}, Created: {notif[4]}')
            conn.close()
                
        except Exception as e:
            print(f'❌ Fehler: {e}')
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_defects_resolved())
