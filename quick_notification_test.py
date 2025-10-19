#!/usr/bin/env python3
"""
SCHNELLER TEST FÜR BENACHRICHTIGUNGEN
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.notification import Notification
from sqlalchemy import select


async def quick_test():
    print("Teste Benachrichtigungen...")
    
    async for db in get_db():
        try:
            # Prüfe bestehende Benachrichtigungen
            result = await db.execute(select(Notification).limit(10))
            notifications = list(result.scalars().all())
            
            print(f"Gefunden: {len(notifications)} Benachrichtigungen")
            
            for n in notifications:
                print(f"  ID: {n.id}, Typ: {n.type}, Empfänger: {n.recipient_id}")
                print(f"  Titel: {n.title}")
                print(f"  Erstellt: {n.created_at}")
                print()
            
            break
            
        except Exception as e:
            print(f"Fehler: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await db.close()


if __name__ == "__main__":
    asyncio.run(quick_test())
