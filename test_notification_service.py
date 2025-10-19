#!/usr/bin/env python3
"""
DEBUG SCRIPT FÜR ROBUSTE BENACHRICHTIGUNGSLÖSUNG

Dieses Script testet die robuste Benachrichtigungslösung direkt.
"""

import asyncio
import sys
import os
from datetime import datetime, date

# Füge das Projekt-Root-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.notification import Notification, NotificationType
from app.services.notification_service import NotificationService
from sqlalchemy import select, and_


async def test_notification_service():
    """
    Testet die NotificationService direkt
    """
    print("="*60)
    print("TEST: NOTIFICATION SERVICE")
    print("="*60)
    
    async for db in get_db():
        try:
            # 1. Prüfe bestehende Benachrichtigungen
            print("\n1. Prüfe bestehende Benachrichtigungen...")
            notifications_result = await db.execute(
                select(Notification).limit(10)
            )
            notifications = list(notifications_result.scalars().all())
            
            print(f"OK {len(notifications)} Benachrichtigungen gefunden:")
            for i, notif in enumerate(notifications, 1):
                print(f"   {i}. ID: {notif.id}, Typ: {notif.type}, Empfaenger: {notif.recipient_id}")
                print(f"      Titel: {notif.title}")
                print(f"      Erstellt: {notif.created_at}")
                print()
            
            # 2. Teste NotificationService Methoden
            print("\n2. Teste NotificationService Methoden...")
            
            if notifications:
                # Teste mit dem ersten Benutzer
                user_id = notifications[0].recipient_id
                print(f"Teste mit Benutzer ID: {user_id}")
                
                # Teste get_notification_stats
                try:
                    stats = await NotificationService.get_notification_stats(db, user_id)
                    print(f"OK Statistiken erhalten:")
                    print(f"   Gesamt: {stats.total_count}")
                    print(f"   Ungelesen: {stats.unread_count}")
                    print(f"   Nicht quittiert: {stats.unacknowledged_count}")
                    print(f"   Dringend: {stats.urgent_count}")
                except Exception as e:
                    print(f"FEHLER bei Statistiken: {e}")
                
                # Teste get_user_notifications
                try:
                    user_notifications = await NotificationService.get_user_notifications(
                        db=db,
                        user_id=user_id,
                        limit=5
                    )
                    print(f"OK {len(user_notifications)} Benachrichtigungen für Benutzer {user_id} gefunden")
                except Exception as e:
                    print(f"FEHLER bei Benutzer-Benachrichtigungen: {e}")
            
            print("\n" + "="*60)
            print("OK NOTIFICATION SERVICE TEST ERFOLGREICH!")
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
    print("Starte Test des Notification Service...")
    
    # Führe Tests aus
    success = asyncio.run(test_notification_service())
    
    if success:
        print("\nTEST ERFOLGREICH!")
    else:
        print("\nTEST FEHLGESCHLAGEN!")
        sys.exit(1)
