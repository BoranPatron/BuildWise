#!/usr/bin/env python3
import asyncio
from app.core.database import get_db
from app.models.notification import Notification, NotificationType
from app.models.appointment_response import AppointmentResponse
from sqlalchemy import select, desc

async def check():
    async for db in get_db():
        # Prüfe alle Notifications
        result = await db.execute(select(Notification).order_by(desc(Notification.created_at)).limit(10))
        notifications = list(result.scalars().all())
        print(f'\n=== ALLE BENACHRICHTIGUNGEN ({len(notifications)}) ===')
        for n in notifications:
            print(f'ID: {n.id}, Typ: {n.type}, Empfaenger: {n.recipient_id}')
            print(f'   Titel: {n.title}')
            print(f'   Erstellt: {n.created_at}')
            print()
        
        # Prüfe Appointment Responses
        resp_result = await db.execute(select(AppointmentResponse).order_by(desc(AppointmentResponse.created_at)).limit(5))
        responses = list(resp_result.scalars().all())
        print(f'\n=== APPOINTMENT RESPONSES ({len(responses)}) ===')
        for r in responses:
            print(f'ID: {r.id}, Appointment: {r.appointment_id}, Provider: {r.service_provider_id}')
            print(f'   Status: {r.status}')
            print(f'   Message: {r.message}')
            print(f'   Responded: {r.responded_at}')
            print()
        
        break

asyncio.run(check())

