#!/usr/bin/env python3
"""
TEST SCRIPT FÜR ROBUSTE BENACHRICHTIGUNGSLÖSUNG

Dieses Script testet die neue robuste Benachrichtigungslösung für Angebote.
Es simuliert verschiedene Szenarien und prüft, ob Benachrichtigungen korrekt erstellt werden.

Verwendung:
    python test_robust_notification_system.py
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


async def test_robust_notification_system():
    """
    Testet die robuste Benachrichtigungslösung
    """
    print("="*80)
    print("TEST: ROBUSTE BENACHRICHTIGUNGSLÖSUNG")
    print("="*80)
    
    async for db in get_db():
        try:
            # 1. Erstelle Test-Bauträger
            print("\n1. Erstelle Test-Bautraeger...")
            bautraeger = User(
                email="test-bautraeger@buildwise.de",
                first_name="Test",
                last_name="Bautraeger",
                company_name="Test Bautraeger GmbH",
                user_type=UserType.PROFESSIONAL,
                user_role=UserRole.BAUTRAEGER,
                role_selected=True,
                role_selected_at=datetime.utcnow()
            )
            db.add(bautraeger)
            await db.commit()
            await db.refresh(bautraeger)
            print(f"OK Bautraeger erstellt: ID {bautraeger.id}")
            
            # 2. Erstelle Test-Projekt
            print("\n2. Erstelle Test-Projekt...")
            project = Project(
                name="Test-Projekt fuer Benachrichtigungen",
                description="Test-Projekt zur Ueberpruefung der robusten Benachrichtigungsloesung",
                owner_id=bautraeger.id,
                project_type=ProjectType.NEW_BUILD,
                status=ProjectStatus.PLANNING
            )
            db.add(project)
            await db.commit()
            await db.refresh(project)
            print(f"OK Projekt erstellt: ID {project.id}")
            
            # 3. Erstelle Test-Gewerk
            print("\n3. Erstelle Test-Gewerk...")
            milestone = Milestone(
                title="Test-Elektroinstallation",
                description="Test-Gewerk für Benachrichtigungstest",
                project_id=project.id,
                category="electrical",
                status="active"
            )
            db.add(milestone)
            await db.commit()
            await db.refresh(milestone)
            print(f"OK Gewerk erstellt: ID {milestone.id}")
            
            # 4. Erstelle Test-Dienstleister
            print("\n4. Erstelle Test-Dienstleister...")
            service_provider = User(
                email="test-dienstleister@buildwise.de",
                first_name="Test",
                last_name="Dienstleister",
                company_name="Test Elektro GmbH",
                user_type=UserType.SERVICE_PROVIDER,
                user_role=UserRole.DIENSTLEISTER,
                role_selected=True,
                role_selected_at=datetime.utcnow()
            )
            db.add(service_provider)
            await db.commit()
            await db.refresh(service_provider)
            print(f"OK Dienstleister erstellt: ID {service_provider.id}")
            
            # 5. Teste Angebotserstellung mit robuster Benachrichtigung
            print("\n5. Teste Angebotserstellung mit robuster Benachrichtigung...")
            
            quote_data = QuoteCreate(
                project_id=project.id,
                milestone_id=milestone.id,
                title="Test-Angebot Elektroinstallation",
                description="Test-Angebot für robuste Benachrichtigungslösung",
                total_amount=25000.0,
                currency="CHF",
                labor_cost=15000.0,
                material_cost=8000.0,
                overhead_cost=2000.0,
                estimated_duration=30,
                start_date=date(2024, 3, 1),
                completion_date=date(2024, 3, 31),
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
            
            # 7. Teste Duplikat-Schutz
            print("\n7. Teste Duplikat-Schutz...")
            
            # Erstelle ein zweites Angebot für dasselbe Gewerk
            quote_data2 = QuoteCreate(
                project_id=project.id,
                milestone_id=milestone.id,
                title="Zweites Test-Angebot",
                description="Zweites Test-Angebot für Duplikat-Test",
                total_amount=28000.0,
                currency="CHF",
                status=QuoteStatus.SUBMITTED
            )
            
            quote2 = await create_quote(db, quote_data2, service_provider.id)
            print(f"OK Zweites Angebot erstellt: ID {quote2.id}")
            
            # Prüfe ob für das zweite Angebot auch eine Benachrichtigung erstellt wurde
            notification2_result = await db.execute(
                select(Notification).where(
                    and_(
                        Notification.related_quote_id == quote2.id,
                        Notification.type == NotificationType.QUOTE_SUBMITTED,
                        Notification.recipient_id == bautraeger.id
                    )
                )
            )
            notification2 = notification2_result.scalar_one_or_none()
            
            if notification2:
                print(f"OK Zweite Benachrichtigung gefunden: ID {notification2.id}")
            else:
                print("FEHLER: KEINE ZWEITE BENACHRICHTIGUNG GEFUNDEN!")
                return False
            
            # 8. Teste Benachrichtigungsstatistiken
            print("\n8. Teste Benachrichtigungsstatistiken...")
            stats = await NotificationService.get_notification_stats(db, bautraeger.id)
            print(f"OK Benachrichtigungsstatistiken:")
            print(f"   Gesamt: {stats.total_count}")
            print(f"   Ungelesen: {stats.unread_count}")
            print(f"   Nicht quittiert: {stats.unacknowledged_count}")
            print(f"   Dringend: {stats.urgent_count}")
            
            # 9. Teste Benachrichtigungsliste
            print("\n9. Teste Benachrichtigungsliste...")
            notifications = await NotificationService.get_user_notifications(
                db=db,
                user_id=bautraeger.id,
                limit=10
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


async def cleanup_test_data():
    """
    Bereinigt Test-Daten nach dem Test
    """
    print("\n" + "="*60)
    print("BEREINIGUNG: Lösche Test-Daten...")
    print("="*60)
    
    async for db in get_db():
        try:
            # Lösche Test-Benachrichtigungen
            from sqlalchemy import delete
            await db.execute(
                delete(Notification).where(
                    Notification.title.like("Test%")
                )
            )
            
            # Lösche Test-Angebote
            await db.execute(
                delete(Quote).where(
                    Quote.title.like("Test%")
                )
            )
            
            # Lösche Test-Gewerke
            await db.execute(
                delete(Milestone).where(
                    Milestone.title.like("Test%")
                )
            )
            
            # Lösche Test-Projekte
            await db.execute(
                delete(Project).where(
                    Project.name.like("Test%")
                )
            )
            
            # Lösche Test-Benutzer
            await db.execute(
                delete(User).where(
                    User.email.like("test-%")
                )
            )
            
            await db.commit()
            print("OK Test-Daten erfolgreich geloescht")
            
        except Exception as e:
            print(f"Fehler beim Loeschen der Test-Daten: {e}")
        
        finally:
            await db.close()


if __name__ == "__main__":
    print("Starte Test der robusten Benachrichtigungslösung...")
    
    # Führe Tests aus
    success = asyncio.run(test_robust_notification_system())
    
    if success:
        print("\nTEST ERFOLGREICH!")
        
        # Frage nach Bereinigung
        cleanup = input("\nMoechten Sie die Test-Daten loeschen? (j/n): ").lower().strip()
        if cleanup in ['j', 'ja', 'y', 'yes']:
            asyncio.run(cleanup_test_data())
    else:
        print("\nTEST FEHLGESCHLAGEN!")
        sys.exit(1)
