#!/usr/bin/env python3
"""
TEST DER ROBUSTEN BENACHRICHTIGUNGSLÖSUNG OHNE ENUM-PROBLEME
"""

import asyncio
import sys
import os
from datetime import datetime, date

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models import User, Project, Milestone, Quote, QuoteStatus
from app.schemas.quote import QuoteCreate
from app.services.quote_service import create_quote
from app.models.notification import Notification, NotificationType
from sqlalchemy import select, and_, text


async def test_without_enum_problems():
    """
    Testet die robuste Benachrichtigungslösung ohne Enum-Probleme
    """
    print("="*60)
    print("TEST DER ROBUSTEN BENACHRICHTIGUNGSLÖSUNG")
    print("="*60)
    
    async for db in get_db():
        try:
            # 1. Finde einen Benutzer mit raw SQL (um Enum-Probleme zu vermeiden)
            print("\n1. Suche Benutzer...")
            user_result = await db.execute(text("SELECT id, email, user_role FROM users LIMIT 1"))
            user_row = user_result.fetchone()
            
            if not user_row:
                print("FEHLER: Kein Benutzer gefunden!")
                return False
            
            user_id = user_row[0]
            user_email = user_row[1]
            user_role = user_row[2]
            
            print(f"OK Benutzer gefunden: ID {user_id}, Email: {user_email}, Role: {user_role}")
            
            # 2. Finde ein Projekt
            print("\n2. Suche Projekt...")
            project_result = await db.execute(text("SELECT id, name, owner_id FROM projects LIMIT 1"))
            project_row = project_result.fetchone()
            
            if not project_row:
                print("FEHLER: Kein Projekt gefunden!")
                return False
            
            project_id = project_row[0]
            project_name = project_row[1]
            owner_id = project_row[2]
            
            print(f"OK Projekt gefunden: ID {project_id}, Name: {project_name}, Owner: {owner_id}")
            
            # 3. Finde ein Gewerk
            print("\n3. Suche Gewerk...")
            milestone_result = await db.execute(text("SELECT id, title, project_id FROM milestones WHERE project_id = :project_id LIMIT 1"), {"project_id": project_id})
            milestone_row = milestone_result.fetchone()
            
            if not milestone_row:
                print("FEHLER: Kein Gewerk gefunden!")
                return False
            
            milestone_id = milestone_row[0]
            milestone_title = milestone_row[1]
            
            print(f"OK Gewerk gefunden: ID {milestone_id}, Titel: {milestone_title}")
            
            # 4. Erstelle ein Test-Angebot direkt mit SQL
            print("\n4. Erstelle Test-Angebot...")
            
            # Erstelle Angebot direkt in der Datenbank
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
            
            # 5. Teste die robuste Benachrichtigungslösung direkt
            print("\n5. Teste robuste Benachrichtigungslösung...")
            
            # Importiere die robuste Funktion
            from app.api.quotes import _ensure_quote_notification_sent
            
            # Hole das Quote-Objekt
            quote_result = await db.execute(select(Quote).where(Quote.id == quote_id))
            quote = quote_result.scalar_one_or_none()
            
            if not quote:
                print("FEHLER: Quote-Objekt nicht gefunden!")
                return False
            
            # Teste die robuste Benachrichtigungslösung
            notification_sent = await _ensure_quote_notification_sent(db, quote)
            
            if notification_sent:
                print("OK Robuste Benachrichtigungslösung erfolgreich!")
            else:
                print("FEHLER: Robuste Benachrichtigungslösung fehlgeschlagen!")
                return False
            
            # 6. Prüfe ob Benachrichtigung erstellt wurde
            print("\n6. Prüfe Benachrichtigung...")
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
                print(f"ERFOLG: Benachrichtigung gefunden!")
                print(f"   ID: {notification.id}")
                print(f"   Titel: {notification.title}")
                print(f"   Empfaenger: {notification.recipient_id}")
                print(f"   Erstellt: {notification.created_at}")
            else:
                print("FEHLER: KEINE BENACHRICHTIGUNG GEFUNDEN!")
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
    success = asyncio.run(test_without_enum_problems())
    
    if success:
        print("\nTEST ERFOLGREICH!")
    else:
        print("\nTEST FEHLGESCHLAGEN!")
        sys.exit(1)
