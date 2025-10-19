#!/usr/bin/env python3
"""
DIREKTER TEST DER ROBUSTEN BENACHRICHTIGUNGSLÖSUNG
"""

import asyncio
import sys
import os
from datetime import datetime, date

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models import User, Project, Milestone, Quote, QuoteStatus
from app.models.user import UserRole, UserType
from app.models.project import ProjectType, ProjectStatus
from app.schemas.quote import QuoteCreate
from app.services.quote_service import create_quote
from app.models.notification import Notification, NotificationType
from sqlalchemy import select, and_


async def test_notification_directly():
    """
    Testet die robuste Benachrichtigungslösung direkt
    """
    print("="*60)
    print("DIREKTER TEST DER ROBUSTEN BENACHRICHTIGUNGSLÖSUNG")
    print("="*60)
    
    async for db in get_db():
        try:
            # 1. Finde einen bestehenden Bauträger
            print("\n1. Suche bestehenden Bautraeger...")
            bautraeger_result = await db.execute(
                select(User).where(User.user_role == UserRole.BAUTRAEGER).limit(1)
            )
            bautraeger = bautraeger_result.scalar_one_or_none()
            
            if not bautraeger:
                print("FEHLER: Kein Bautraeger gefunden!")
                return False
            
            print(f"OK Bautraeger gefunden: ID {bautraeger.id}")
            
            # 2. Finde ein bestehendes Projekt
            print("\n2. Suche bestehendes Projekt...")
            project_result = await db.execute(
                select(Project).where(Project.owner_id == bautraeger.id).limit(1)
            )
            project = project_result.scalar_one_or_none()
            
            if not project:
                print("FEHLER: Kein Projekt gefunden!")
                return False
            
            print(f"OK Projekt gefunden: ID {project.id}")
            
            # 3. Finde ein bestehendes Gewerk
            print("\n3. Suche bestehendes Gewerk...")
            milestone_result = await db.execute(
                select(Milestone).where(Milestone.project_id == project.id).limit(1)
            )
            milestone = milestone_result.scalar_one_or_none()
            
            if not milestone:
                print("FEHLER: Kein Gewerk gefunden!")
                return False
            
            print(f"OK Gewerk gefunden: ID {milestone.id}")
            
            # 4. Finde einen bestehenden Dienstleister
            print("\n4. Suche bestehenden Dienstleister...")
            service_provider_result = await db.execute(
                select(User).where(User.user_role == UserRole.DIENSTLEISTER).limit(1)
            )
            service_provider = service_provider_result.scalar_one_or_none()
            
            if not service_provider:
                print("FEHLER: Kein Dienstleister gefunden!")
                return False
            
            print(f"OK Dienstleister gefunden: ID {service_provider.id}")
            
            # 5. Erstelle ein Test-Angebot
            print("\n5. Erstelle Test-Angebot...")
            
            quote_data = QuoteCreate(
                project_id=project.id,
                milestone_id=milestone.id,
                title="TEST-ANGEBOT FÜR BENACHRICHTIGUNG",
                description="Direkter Test der robusten Benachrichtigungslösung",
                total_amount=10000.0,
                currency="CHF",
                status=QuoteStatus.SUBMITTED
            )
            
            # Erstelle Angebot - dies sollte die robuste Benachrichtigung auslösen
            quote = await create_quote(db, quote_data, service_provider.id)
            print(f"OK Angebot erstellt: ID {quote.id}")
            
            # 6. Prüfe sofort nach Benachrichtigung
            print("\n6. Prüfe Benachrichtigung...")
            notification_result = await db.execute(
                select(Notification).where(
                    and_(
                        Notification.related_quote_id == quote.id,
                        Notification.type == NotificationType.QUOTE_SUBMITTED
                    )
                )
            )
            notification = notification_result.scalar_one_or_none()
            
            if notification:
                print(f"ERFOLG: Benachrichtigung gefunden!")
                print(f"   ID: {notification.id}")
                print(f"   Titel: {notification.title}")
                print(f"   Empfaenger: {notification.recipient_id}")
                print(f"   Erstellt: {notification.created_at}")
            else:
                print("FEHLER: KEINE BENACHRICHTIGUNG GEFUNDEN!")
                
                # Debug: Prüfe alle Benachrichtigungen
                all_notifications_result = await db.execute(select(Notification))
                all_notifications = list(all_notifications_result.scalars().all())
                print(f"Debug: {len(all_notifications)} Benachrichtigungen insgesamt in DB")
                
                return False
            
            print("\n" + "="*60)
            print("TEST ERFOLGREICH!")
            print("Die robuste Benachrichtigungslösung funktioniert!")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"\nFEHLER BEIM TEST: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            await db.close()


if __name__ == "__main__":
    success = asyncio.run(test_notification_directly())
    
    if success:
        print("\n✅ TEST ERFOLGREICH!")
    else:
        print("\n❌ TEST FEHLGESCHLAGEN!")
        sys.exit(1)
