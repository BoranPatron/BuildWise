#!/usr/bin/env python3
"""
EINFACHER TEST FÜR ROBUSTE BENACHRICHTIGUNGSLÖSUNG

Dieses Script testet die neue robuste Benachrichtigungslösung mit bestehenden Daten.
"""

import asyncio
import sys
import os
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession

# Füge das Projekt-Root-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models import User, Project, Milestone, Quote, QuoteStatus
from app.models.user import UserType, UserRole
from app.models.project import ProjectType, ProjectStatus
from app.schemas.quote import QuoteCreate
from app.services.quote_service import create_quote, get_quote_by_id
from app.services.notification_service import NotificationService
from app.models.notification import Notification, NotificationType
from sqlalchemy import select, and_


async def test_with_existing_data():
    """
    Testet die robuste Benachrichtigungslösung mit bestehenden Daten
    """
    print("="*80)
    print("TEST: ROBUSTE BENACHRICHTIGUNGSLÖSUNG (mit bestehenden Daten)")
    print("="*80)
    
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
            
            print(f"OK Bautraeger gefunden: ID {bautraeger.id}, Email: {bautraeger.email}")
            
            # 2. Finde ein bestehendes Projekt des Bauträgers
            print("\n2. Suche bestehendes Projekt...")
            project_result = await db.execute(
                select(Project).where(Project.owner_id == bautraeger.id).limit(1)
            )
            project = project_result.scalar_one_or_none()
            
            if not project:
                print("FEHLER: Kein Projekt für Bautraeger gefunden!")
                return False
            
            print(f"OK Projekt gefunden: ID {project.id}, Name: {project.name}")
            
            # 3. Finde ein bestehendes Gewerk
            print("\n3. Suche bestehendes Gewerk...")
            milestone_result = await db.execute(
                select(Milestone).where(Milestone.project_id == project.id).limit(1)
            )
            milestone = milestone_result.scalar_one_or_none()
            
            if not milestone:
                print("FEHLER: Kein Gewerk für Projekt gefunden!")
                return False
            
            print(f"OK Gewerk gefunden: ID {milestone.id}, Titel: {milestone.title}")
            
            # 4. Finde einen bestehenden Dienstleister
            print("\n4. Suche bestehenden Dienstleister...")
            service_provider_result = await db.execute(
                select(User).where(User.user_role == UserRole.DIENSTLEISTER).limit(1)
            )
            service_provider = service_provider_result.scalar_one_or_none()
            
            if not service_provider:
                print("FEHLER: Kein Dienstleister gefunden!")
                return False
            
            print(f"OK Dienstleister gefunden: ID {service_provider.id}, Email: {service_provider.email}")
            
            # 5. Teste Angebotserstellung mit robuster Benachrichtigung
            print("\n5. Teste Angebotserstellung mit robuster Benachrichtigung...")
            
            quote_data = QuoteCreate(
                project_id=project.id,
                milestone_id=milestone.id,
                title="Test-Angebot fuer robuste Benachrichtigung",
                description="Test-Angebot zur Ueberpruefung der robusten Benachrichtigungsloesung",
                total_amount=15000.0,
                currency="CHF",
                labor_cost=8000.0,
                material_cost=5000.0,
                overhead_cost=2000.0,
                estimated_duration=20,
                start_date=date(2024, 3, 1),
                completion_date=date(2024, 3, 21),
                payment_terms="30 Tage nach Rechnung",
                warranty_period=24,
                company_name="Test Elektro GmbH",
                contact_person="Test Dienstleister",
                phone="+41 123 456789",
                email="test@test-elektro.ch",
                website="www.test-elektro.ch",
                status=QuoteStatus.SUBMITTED
            )
            
            # Erstelle Angebot (dies sollte automatisch eine Benachrichtigung erstellen)
            quote = await create_quote(db, quote_data, service_provider.id)
            print(f"OK Angebot erstellt: ID {quote.id}")
            
            # 6. Prüfe ob Benachrichtigung erstellt wurde
            print("\n6. Prüfe Benachrichtigung...")
            notification_result = await db.execute(
                select(Notification).where(
                    and_(
                        Notification.related_quote_id == quote.id,
                        Notification.type == NotificationType.QUOTE_SUBMITTED,
                        Notification.recipient_id == bautraeger.id
                    )
                )
            )
            notification = notification_result.scalar_one_or_none()
            
            if notification:
                print(f"OK Benachrichtigung gefunden: ID {notification.id}")
                print(f"   Titel: {notification.title}")
                print(f"   Nachricht: {notification.message}")
                print(f"   Empfaenger: {notification.recipient_id}")
                print(f"   Erstellt: {notification.created_at}")
                print(f"   Gelesen: {notification.is_read}")
                print(f"   Quittiert: {notification.is_acknowledged}")
            else:
                print("FEHLER: KEINE BENACHRICHTIGUNG GEFUNDEN!")
                return False
            
            # 7. Teste Benachrichtigungsstatistiken
            print("\n7. Teste Benachrichtigungsstatistiken...")
            stats = await NotificationService.get_notification_stats(db, bautraeger.id)
            print(f"OK Benachrichtigungsstatistiken:")
            print(f"   Gesamt: {stats.total_count}")
            print(f"   Ungelesen: {stats.unread_count}")
            print(f"   Nicht quittiert: {stats.unacknowledged_count}")
            print(f"   Dringend: {stats.urgent_count}")
            
            # 8. Teste Benachrichtigungsliste
            print("\n8. Teste Benachrichtigungsliste...")
            notifications = await NotificationService.get_user_notifications(
                db=db,
                user_id=bautraeger.id,
                limit=5
            )
            print(f"OK {len(notifications)} Benachrichtigungen fuer Bautraeger gefunden:")
            for i, notif in enumerate(notifications, 1):
                print(f"   {i}. {notif.title} - {notif.type} - {notif.created_at}")
            
            print("\n" + "="*80)
            print("OK ALLE TESTS ERFOLGREICH!")
            print("Die robuste Benachrichtigungsloesung funktioniert korrekt.")
            print("="*80)
            
            return True
            
        except Exception as e:
            print(f"\nFEHLER BEIM TEST: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            await db.close()


if __name__ == "__main__":
    print("Starte Test der robusten Benachrichtigungslösung...")
    
    # Führe Tests aus
    success = asyncio.run(test_with_existing_data())
    
    if success:
        print("\nTEST ERFOLGREICH!")
    else:
        print("\nTEST FEHLGESCHLAGEN!")
        sys.exit(1)
