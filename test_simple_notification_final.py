#!/usr/bin/env python3
"""
EINFACHER TEST FÜR BENACHRICHTIGUNGEN
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.notification import Notification, NotificationType
from sqlalchemy import select, and_, text


async def simple_notification_test():
    """
    Einfacher Test für Benachrichtigungen
    """
    print("="*60)
    print("EINFACHER TEST FÜR BENACHRICHTIGUNGEN")
    print("="*60)
    
    async for db in get_db():
        try:
            # 1. Prüfe bestehende Benachrichtigungen
            print("\n1. Prüfe bestehende Benachrichtigungen...")
            result = await db.execute(select(Notification).limit(10))
            notifications = list(result.scalars().all())
            
            print(f"Gefunden: {len(notifications)} Benachrichtigungen")
            
            for n in notifications:
                print(f"  ID: {n.id}, Typ: {n.type}, Empfaenger: {n.recipient_id}")
                print(f"  Titel: {n.title}")
                print(f"  Erstellt: {n.created_at}")
                print()
            
            # 2. Teste NotificationService direkt
            print("\n2. Teste NotificationService direkt...")
            
            from app.services.notification_service import NotificationService
            
            # Finde einen Benutzer
            user_result = await db.execute(text("SELECT id FROM users LIMIT 1"))
            user_row = user_result.fetchone()
            
            if not user_row:
                print("FEHLER: Kein Benutzer gefunden!")
                return False
            
            user_id = user_row[0]
            print(f"OK Benutzer gefunden: ID {user_id}")
            
            # Finde ein Projekt
            project_result = await db.execute(text("SELECT id, owner_id FROM projects LIMIT 1"))
            project_row = project_result.fetchone()
            
            if not project_row:
                print("FEHLER: Kein Projekt gefunden!")
                return False
            
            project_id = project_row[0]
            owner_id = project_row[1]
            print(f"OK Projekt gefunden: ID {project_id}, Owner: {owner_id}")
            
            # Finde ein Gewerk
            milestone_result = await db.execute(text("SELECT id, title FROM milestones WHERE project_id = :project_id LIMIT 1"), {"project_id": project_id})
            milestone_row = milestone_result.fetchone()
            
            if not milestone_row:
                print("FEHLER: Kein Gewerk gefunden!")
                return False
            
            milestone_id = milestone_row[0]
            milestone_title = milestone_row[1]
            print(f"OK Gewerk gefunden: ID {milestone_id}, Titel: {milestone_title}")
            
            # Erstelle ein Test-Angebot
            print("\n3. Erstelle Test-Angebot...")
            
            quote_insert_result = await db.execute(text("""
                INSERT INTO quotes (
                    project_id, milestone_id, service_provider_id, title, description,
                    total_amount, currency, status, created_at, updated_at
                ) VALUES (
                    :project_id, :milestone_id, :service_provider_id, :title, :description,
                    :total_amount, :currency, :status, :created_at, :updated_at
                )
            """), {
                "project_id": project_id,
                "milestone_id": milestone_id,
                "service_provider_id": user_id,
                "title": "TEST-ANGEBOT FÜR BENACHRICHTIGUNG",
                "description": "Direkter Test der robusten Benachrichtigungslösung",
                "total_amount": 10000.0,
                "currency": "CHF",
                "status": "submitted",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            
            await db.commit()
            
            # Hole die Quote-ID
            quote_id_result = await db.execute(text("SELECT id FROM quotes WHERE title = :title ORDER BY id DESC LIMIT 1"), {"title": "TEST-ANGEBOT FÜR BENACHRICHTIGUNG"})
            quote_id_row = quote_id_result.fetchone()
            
            if not quote_id_row:
                print("FEHLER: Angebot konnte nicht erstellt werden!")
                return False
            
            quote_id = quote_id_row[0]
            print(f"OK Angebot erstellt: ID {quote_id}")
            
            # 4. Teste NotificationService direkt
            print("\n4. Teste NotificationService direkt...")
            
            try:
                notification = await NotificationService.create_quote_submitted_notification(
                    db=db,
                    quote_id=quote_id,
                    recipient_id=owner_id
                )
                
                print(f"ERFOLG: Benachrichtigung erstellt!")
                print(f"   ID: {notification.id}")
                print(f"   Titel: {notification.title}")
                print(f"   Empfaenger: {notification.recipient_id}")
                print(f"   Erstellt: {notification.created_at}")
                
            except Exception as e:
                print(f"FEHLER beim Erstellen der Benachrichtigung: {e}")
                import traceback
                traceback.print_exc()
                return False
            
            # 5. Prüfe ob Benachrichtigung in der Datenbank ist
            print("\n5. Prüfe Benachrichtigung in der Datenbank...")
            
            notification_result = await db.execute(
                select(Notification).where(
                    and_(
                        Notification.related_quote_id == quote_id,
                        Notification.type == NotificationType.QUOTE_SUBMITTED
                    )
                )
            )
            notification = notification_result.scalar_one_or_none()
            
            if notification:
                print(f"ERFOLG: Benachrichtigung in Datenbank gefunden!")
                print(f"   ID: {notification.id}")
                print(f"   Titel: {notification.title}")
                print(f"   Empfaenger: {notification.recipient_id}")
            else:
                print("FEHLER: KEINE BENACHRICHTIGUNG IN DATENBANK GEFUNDEN!")
                return False
            
            print("\n" + "="*60)
            print("TEST ERFOLGREICH!")
            print("Die Benachrichtigungslösung funktioniert!")
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
    success = asyncio.run(simple_notification_test())
    
    if success:
        print("\nTEST ERFOLGREICH!")
    else:
        print("\nTEST FEHLGESCHLAGEN!")
        sys.exit(1)
