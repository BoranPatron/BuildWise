#!/usr/bin/env python3
import asyncio
from app.core.database import get_db
from app.models.notification import Notification
from sqlalchemy import select, desc

async def check():
    async for db in get_db():
        result = await db.execute(select(Notification).order_by(desc(Notification.created_at)).limit(10))
        notifications = list(result.scalars().all())
        print(f'Gefunden: {len(notifications)} Benachrichtigungen')
        for n in notifications:
            print(f'ID: {n.id}, Typ: {n.type}, Empfaenger: {n.recipient_id}, Titel: {n.title}')
            print(f'   Erstellt: {n.created_at}, Gelesen: {n.is_read}, Quittiert: {n.is_acknowledged}')
        break

asyncio.run(check())

