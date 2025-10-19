#!/usr/bin/env python3
import asyncio
import sqlite3
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

async def create_missing_defects_notification():
    """Erstelle nachträglich eine Benachrichtigung für die bereits gemeldete Mängelbehebung"""
    
    # Erstelle async engine
    engine = create_async_engine("sqlite+aiosqlite:///buildwise.db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            # Importiere benötigte Modelle
            from app.services.notification_service import NotificationService
            from app.schemas.notification import NotificationCreate
            from app.models.notification import NotificationType, NotificationPriority
            from app.models.milestone import Milestone
            from app.models.project import Project
            
            # Hole Milestone 1
            milestone_stmt = select(Milestone).where(Milestone.id == 1)
            milestone_result = await db.execute(milestone_stmt)
            milestone = milestone_result.scalar_one_or_none()
            
            if not milestone:
                print("❌ Milestone 1 nicht gefunden")
                return
                
            print(f"✅ Milestone gefunden: {milestone.title} (Status: {milestone.completion_status})")
            
            # Hole Projekt-Informationen
            project_stmt = select(Project).where(Project.id == milestone.project_id)
            project_result = await db.execute(project_stmt)
            project = project_result.scalar_one_or_none()
            
            if not project:
                print("❌ Projekt nicht gefunden")
                return
                
            print(f"✅ Projekt gefunden: ID {project.id} (Bauträger: {project.owner_id})")
            
            # Prüfe ob bereits eine Benachrichtigung existiert
            from app.models.notification import Notification
            existing_notif_stmt = select(Notification).where(
                Notification.recipient_id == project.owner_id,
                Notification.type == NotificationType.DEFECTS_RESOLVED,
                Notification.related_milestone_id == milestone.id
            )
            existing_notif_result = await db.execute(existing_notif_stmt)
            existing_notif = existing_notif_result.scalar_one_or_none()
            
            if existing_notif:
                print(f"ℹ️ Benachrichtigung existiert bereits: {existing_notif.id}")
                return
            
            # Erstelle die fehlende Benachrichtigung
            notification_data = NotificationCreate(
                recipient_id=project.owner_id,
                type=NotificationType.DEFECTS_RESOLVED,
                title='Mängelbehebung gemeldet',
                message=f'Der Dienstleister hat die Mängelbehebung für "{milestone.title}" gemeldet. Sie können nun die finale Abnahme durchführen.',
                priority=NotificationPriority.HIGH,
                related_milestone_id=milestone.id,
                related_project_id=milestone.project_id
            )
            
            notification = await NotificationService.create_notification(
                db=db,
                notification_data=notification_data
            )
            
            print(f"✅ Nachträgliche Benachrichtigung erstellt!")
            print(f"   ID: {notification.id}")
            print(f"   Empfänger: {notification.recipient_id}")
            print(f"   Typ: {notification.type}")
            print(f"   Titel: {notification.title}")
            
            # Bestätige in der Datenbank
            await db.commit()
            
            print(f"\n🎉 ERFOLGREICH! Bauträger {project.owner_id} sollte jetzt die Benachrichtigung sehen.")
            
        except Exception as e:
            print(f"❌ Fehler: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(create_missing_defects_notification())
