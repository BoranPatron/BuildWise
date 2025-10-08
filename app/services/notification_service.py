from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from ..models.notification import Notification, NotificationType, NotificationPriority
from ..models.user import User
from ..models.quote import Quote
from ..models.project import Project
from ..models.milestone import Milestone
from ..schemas.notification import (
    NotificationCreate, NotificationUpdate, NotificationRead, NotificationStats,
    QuoteNotificationData
)

class NotificationService:
    """Service für Benachrichtigungsverwaltung"""
    
    @staticmethod
    async def create_notification(
        db: AsyncSession,
        notification_data: NotificationCreate
    ) -> Notification:
        """Erstellt eine neue Benachrichtigung"""
        db_notification = Notification(**notification_data.dict())
        db.add(db_notification)
        await db.commit()
        await db.refresh(db_notification)
        return db_notification
    
    @staticmethod
    async def create_quote_submitted_notification(
        db: AsyncSession,
        quote_id: int,
        recipient_id: int
    ) -> Notification:
        """
        Erstellt eine Benachrichtigung für ein neu eingreichtes Angebot
        
        Args:
            db: Datenbank-Session
            quote_id: ID des eingereichten Angebots
            recipient_id: ID des Empfängers (normalerweise der Bauträger)
        """
        # Lade Quote mit allen relevanten Daten
        from ..models.user import User
        result = await db.execute(
            select(Quote)
            .options(
                selectinload(Quote.milestone),
                selectinload(Quote.project)
            )
            .where(Quote.id == quote_id)
        )
        quote = result.scalar_one_or_none()
        
        if not quote:
            raise ValueError(f"Quote mit ID {quote_id} nicht gefunden")
        
        # Lade Service Provider separat
        service_provider = None
        if quote.service_provider_id:
            sp_result = await db.execute(
                select(User).where(User.id == quote.service_provider_id)
            )
            service_provider = sp_result.scalar_one_or_none()
        
        # Erstelle Service Provider Name
        service_provider_name = "Unbekannter Dienstleister"
        if service_provider:
            if service_provider.company_name:
                service_provider_name = service_provider.company_name
            else:
                service_provider_name = f"{service_provider.first_name or ''} {service_provider.last_name or ''}".strip()
                if not service_provider_name:
                    service_provider_name = f"Benutzer #{service_provider.id}"
        
        # Erstelle Benachrichtigungsdaten
        notification_data = QuoteNotificationData(
            quote_id=quote.id,
            quote_title=quote.title or f"Angebot #{quote.id}",
            service_provider_name=service_provider_name,
            project_name=quote.project.name if quote.project else "Unbekanntes Projekt",
            milestone_title=quote.milestone.title if quote.milestone else "Unbekanntes Gewerk",
            total_amount=quote.total_amount,
            currency=quote.currency or "CHF"
        )
        
        # Erstelle Benachrichtigung
        notification = Notification(
            recipient_id=recipient_id,
            type=NotificationType.QUOTE_SUBMITTED,
            priority=NotificationPriority.HIGH,
            title=f"Neues Angebot eingereicht",
            message=f"{notification_data.service_provider_name} hat ein Angebot für '{notification_data.milestone_title}' eingereicht. Angebotssumme: {notification_data.total_amount} {notification_data.currency}",
            data=notification_data.json(),
            related_quote_id=quote_id,
            related_project_id=quote.project_id,
            related_milestone_id=quote.milestone_id
        )
        
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        
        return notification
    
    @staticmethod
    async def create_quote_revised_notification(
        db: AsyncSession,
        quote_id: int,
        recipient_id: int,
        milestone_id: Optional[int] = None
    ) -> Notification:
        """
        Erstellt eine Benachrichtigung für ein überarbeitetes Angebot nach Besichtigung
        
        Args:
            db: Datenbank-Session
            quote_id: ID des überarbeiteten Angebots
            recipient_id: ID des Empfängers (normalerweise der Bauträger)
            milestone_id: ID des Gewerks (optional)
        """
        # Lade Quote mit allen relevanten Daten
        from ..models.user import User
        result = await db.execute(
            select(Quote)
            .options(
                selectinload(Quote.milestone),
                selectinload(Quote.project)
            )
            .where(Quote.id == quote_id)
        )
        quote = result.scalar_one_or_none()
        
        if not quote:
            raise ValueError(f"Quote mit ID {quote_id} nicht gefunden")
        
        # Lade Service Provider separat
        service_provider = None
        if quote.service_provider_id:
            sp_result = await db.execute(
                select(User).where(User.id == quote.service_provider_id)
            )
            service_provider = sp_result.scalar_one_or_none()
        
        # Erstelle Service Provider Name
        service_provider_name = "Unbekannter Dienstleister"
        if service_provider:
            if service_provider.company_name:
                service_provider_name = service_provider.company_name
            else:
                service_provider_name = f"{service_provider.first_name or ''} {service_provider.last_name or ''}".strip()
                if not service_provider_name:
                    service_provider_name = f"Benutzer #{service_provider.id}"
        
        # Erstelle Benachrichtigungsdaten mit Revisions-Info
        notification_data = QuoteNotificationData(
            quote_id=quote.id,
            quote_title=quote.title or f"Angebot #{quote.id}",
            service_provider_name=service_provider_name,
            project_name=quote.project.name if quote.project else "Unbekanntes Projekt",
            milestone_title=quote.milestone.title if quote.milestone else "Unbekanntes Gewerk",
            total_amount=quote.total_amount,
            currency=quote.currency or "CHF"
        )
        
        # Erstelle Benachrichtigung mit neuem Typ
        notification = Notification(
            recipient_id=recipient_id,
            type=NotificationType.QUOTE_REVISED,  # Neuer Benachrichtigungstyp
            priority=NotificationPriority.HIGH,
            title=f"Angebot nach Besichtigung überarbeitet",
            message=f"{notification_data.service_provider_name} hat sein Angebot für '{notification_data.milestone_title}' nach der Besichtigung überarbeitet. Neue Angebotssumme: {notification_data.total_amount} {notification_data.currency} (Überarbeitung #{quote.revision_count})",
            data=notification_data.json(),
            related_quote_id=quote_id,
            related_project_id=quote.project_id,
            related_milestone_id=milestone_id or quote.milestone_id
        )
        
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        
        print(f"[SUCCESS] Benachrichtigung für überarbeitetes Angebot {quote_id} erstellt (Revision #{quote.revision_count})")
        return notification
    
    @staticmethod
    async def create_resource_allocated_notification(
        db: AsyncSession,
        allocation_id: int,
        service_provider_id: int
    ) -> Notification:
        """
        Erstellt eine Benachrichtigung für eine Ressourcen-Zuordnung zu einer Ausschreibung
        
        Args:
            db: Datenbank-Session
            allocation_id: ID der Ressourcen-Zuordnung
            service_provider_id: ID des Dienstleisters (Empfänger)
        """
        # Lade ResourceAllocation mit allen relevanten Daten
        from ..models.resource import ResourceAllocation
        from ..models.milestone import Milestone
        from ..models.project import Project
        from ..models.user import User
        
        result = await db.execute(
            select(ResourceAllocation)
            .options(
                selectinload(ResourceAllocation.resource),
                selectinload(ResourceAllocation.trade)
            )
            .where(ResourceAllocation.id == allocation_id)
        )
        allocation = result.scalar_one_or_none()
        
        if not allocation:
            raise ValueError(f"ResourceAllocation mit ID {allocation_id} nicht gefunden")
        
        # Prüfe ob trade_id gültig ist (nicht 0 oder None)
        if not allocation.trade_id or allocation.trade_id == 0:
            raise ValueError(f"ResourceAllocation {allocation_id} hat ungültige trade_id: {allocation.trade_id}")
        
        # Lade Projekt-Details
        project = None
        if allocation.trade and allocation.trade.project_id:
            project_result = await db.execute(
                select(Project).where(Project.id == allocation.trade.project_id)
            )
            project = project_result.scalar_one_or_none()
        
        # Lade Bauträger-Details
        bautraeger = None
        if project and project.owner_id:
            bautraeger_result = await db.execute(
                select(User).where(User.id == project.owner_id)
            )
            bautraeger = bautraeger_result.scalar_one_or_none()
        
        # Erstelle Bauträger Name (Vorname + Nachname + optional Firmenname)
        bautraeger_name = "Unbekannter Bauträger"
        bautraeger_full_name = ""
        bautraeger_company = ""
        
        if bautraeger:
            # Name: Vorname + Nachname
            full_name_parts = []
            if bautraeger.first_name:
                full_name_parts.append(bautraeger.first_name)
            if bautraeger.last_name:
                full_name_parts.append(bautraeger.last_name)
            
            bautraeger_full_name = " ".join(full_name_parts) if full_name_parts else f"Benutzer #{bautraeger.id}"
            
            # Firmenname separat
            if bautraeger.company_name:
                bautraeger_company = bautraeger.company_name
                bautraeger_name = f"{bautraeger_full_name} ({bautraeger.company_name})"
            else:
                bautraeger_name = bautraeger_full_name
        
        # Erstelle Benachrichtigungsdaten
        notification_data = {
            "allocation_id": allocation.id,
            "resource_id": allocation.resource_id,
            "trade_id": allocation.trade_id,
            "trade_title": allocation.trade.title if allocation.trade else "Unbekanntes Gewerk",
            "project_name": project.name if project else "Unbekanntes Projekt",
            "project_id": project.id if project else None,
            "bautraeger_name": bautraeger_name,
            "bautraeger_full_name": bautraeger_full_name,
            "bautraeger_company": bautraeger_company,
            "allocated_start_date": allocation.allocated_start_date.isoformat() if allocation.allocated_start_date else None,
            "allocated_end_date": allocation.allocated_end_date.isoformat() if allocation.allocated_end_date else None,
            "allocated_person_count": allocation.allocated_person_count,
            "allocation_status": allocation.allocation_status.value if allocation.allocation_status else "pre_selected"
        }
        
        # Erstelle Benachrichtigung mit besserer Nachricht
        trade_title = allocation.trade.title if allocation.trade else "Unbekanntes Gewerk"
        project_name = project.name if project else "Unbekanntes Projekt"
        
        # Erstelle message mit Fallback-Werten
        message = f"Ihre Ressource wurde der Ausschreibung '{trade_title}' im Projekt '{project_name}' zugeordnet."
        
        notification = Notification(
            recipient_id=service_provider_id,
            type=NotificationType.RESOURCE_ALLOCATED,
            priority=NotificationPriority.HIGH,
            title=f"Ressource einer Ausschreibung zugeordnet",
            message=message,
            data=json.dumps(notification_data),
            related_project_id=project.id if project else None,
            related_milestone_id=allocation.trade_id
        )
        
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        
        return notification
    
    @staticmethod
    async def create_tender_invitation_notification(
        db: AsyncSession,
        allocation_id: int,
        service_provider_id: int,
        deadline: datetime = None
    ) -> Notification:
        """
        Erstellt eine Benachrichtigung für eine Einladung zur Angebotsabgabe
        
        Args:
            db: Datenbank-Session
            allocation_id: ID der Ressourcen-Zuordnung
            service_provider_id: ID des Dienstleisters (Empfänger)
            deadline: Abgabefrist für das Angebot
        """
        # Lade ResourceAllocation mit allen relevanten Daten
        from ..models.resource import ResourceAllocation
        from ..models.milestone import Milestone
        from ..models.project import Project
        from ..models.user import User
        
        result = await db.execute(
            select(ResourceAllocation)
            .options(
                selectinload(ResourceAllocation.resource),
                selectinload(ResourceAllocation.trade)
            )
            .where(ResourceAllocation.id == allocation_id)
        )
        allocation = result.scalar_one_or_none()
        
        if not allocation:
            raise ValueError(f"ResourceAllocation mit ID {allocation_id} nicht gefunden")
        
        # Lade Projekt-Details
        project = None
        if allocation.trade and allocation.trade.project_id:
            project_result = await db.execute(
                select(Project).where(Project.id == allocation.trade.project_id)
            )
            project = project_result.scalar_one_or_none()
        
        # Lade Bauträger-Details
        bautraeger = None
        if project and project.owner_id:
            bautraeger_result = await db.execute(
                select(User).where(User.id == project.owner_id)
            )
            bautraeger = bautraeger_result.scalar_one_or_none()
        
        # Erstelle Bauträger Name
        bautraeger_name = "Unbekannter Bauträger"
        if bautraeger:
            if bautraeger.company_name:
                bautraeger_name = bautraeger.company_name
            else:
                bautraeger_name = f"{bautraeger.first_name or ''} {bautraeger.last_name or ''}".strip()
                if not bautraeger_name:
                    bautraeger_name = f"Bauträger #{bautraeger.id}"
        
        # Erstelle Benachrichtigungsdaten
        notification_data = {
            "allocation_id": allocation.id,
            "resource_id": allocation.resource_id,
            "trade_id": allocation.trade_id,
            "trade_title": allocation.trade.title if allocation.trade else "Unbekanntes Gewerk",
            "project_name": project.name if project else "Unbekanntes Projekt",
            "bautraeger_name": bautraeger_name,
            "deadline": deadline.isoformat() if deadline else None,
            "allocated_start_date": allocation.allocated_start_date.isoformat() if allocation.allocated_start_date else None,
            "allocated_end_date": allocation.allocated_end_date.isoformat() if allocation.allocated_end_date else None,
            "allocated_person_count": allocation.allocated_person_count,
            "allocation_status": allocation.allocation_status.value if allocation.allocation_status else "invited"
        }
        
        # Erstelle Benachrichtigung
        deadline_text = f" Abgabefrist: {deadline.strftime('%d.%m.%Y %H:%M')}" if deadline else ""
        notification = Notification(
            recipient_id=service_provider_id,
            type=NotificationType.TENDER_INVITATION,
            priority=NotificationPriority.URGENT,
            title=f"Einladung zur Angebotsabgabe",
            message=f"Sie wurden eingeladen, ein Angebot für '{allocation.trade.title if allocation.trade else 'Unbekanntes Gewerk'}' im Projekt '{project.name if project else 'Unbekanntes Projekt'}' abzugeben.{deadline_text}",
            data=json.dumps(notification_data),
            related_project_id=project.id if project else None,
            related_milestone_id=allocation.trade_id
        )
        
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        
        return notification
    
    @staticmethod
    async def get_user_notifications(
        db: AsyncSession,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
        unacknowledged_only: bool = False
    ) -> List[Notification]:
        """Holt Benachrichtigungen für einen Benutzer"""
        query = select(Notification).where(Notification.recipient_id == user_id)
        
        if unread_only:
            query = query.where(Notification.is_read == False)
        
        if unacknowledged_only:
            query = query.where(Notification.is_acknowledged == False)
        
        query = query.order_by(desc(Notification.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_notification_stats(db: AsyncSession, user_id: int) -> NotificationStats:
        """Holt Statistiken über Benachrichtigungen eines Benutzers"""
        base_query = select(func.count(Notification.id)).where(Notification.recipient_id == user_id)
        
        # Gesamtanzahl
        total_result = await db.execute(base_query)
        total_count = total_result.scalar() or 0
        
        # Ungelesene
        unread_result = await db.execute(
            base_query.where(Notification.is_read == False)
        )
        unread_count = unread_result.scalar() or 0
        
        # Nicht quittierte
        unacknowledged_result = await db.execute(
            base_query.where(Notification.is_acknowledged == False)
        )
        unacknowledged_count = unacknowledged_result.scalar() or 0
        
        # Dringende
        urgent_result = await db.execute(
            base_query.where(
                and_(
                    Notification.priority == NotificationPriority.URGENT,
                    Notification.is_acknowledged == False
                )
            )
        )
        urgent_count = urgent_result.scalar() or 0
        
        return NotificationStats(
            total_count=total_count,
            unread_count=unread_count,
            unacknowledged_count=unacknowledged_count,
            urgent_count=urgent_count
        )
    
    @staticmethod
    async def mark_notification_as_read(
        db: AsyncSession,
        notification_id: int,
        user_id: int
    ) -> Optional[Notification]:
        """Markiert eine Benachrichtigung als gelesen"""
        result = await db.execute(
            select(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.recipient_id == user_id
                )
            )
        )
        notification = result.scalar_one_or_none()
        
        if notification:
            notification.mark_as_read()
            await db.commit()
            await db.refresh(notification)
        
        return notification
    
    @staticmethod
    async def acknowledge_notification(
        db: AsyncSession,
        notification_id: int,
        user_id: int
    ) -> Optional[Notification]:
        """Quittiert eine Benachrichtigung"""
        result = await db.execute(
            select(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.recipient_id == user_id
                )
            )
        )
        notification = result.scalar_one_or_none()
        
        if notification:
            notification.acknowledge()
            await db.commit()
            await db.refresh(notification)
        
        return notification
    
    @staticmethod
    async def mark_all_as_read(db: AsyncSession, user_id: int) -> int:
        """Markiert alle Benachrichtigungen eines Benutzers als gelesen"""
        from sqlalchemy import update
        
        result = await db.execute(
            update(Notification)
            .where(
                and_(
                    Notification.recipient_id == user_id,
                    Notification.is_read == False
                )
            )
            .values(is_read=True, read_at=datetime.utcnow())
        )
        
        await db.commit()
        return result.rowcount
    
    @staticmethod
    async def acknowledge_all(db: AsyncSession, user_id: int) -> int:
        """Quittiert alle Benachrichtigungen eines Benutzers"""
        from sqlalchemy import update
        
        now = datetime.utcnow()
        result = await db.execute(
            update(Notification)
            .where(
                and_(
                    Notification.recipient_id == user_id,
                    Notification.is_acknowledged == False
                )
            )
            .values(
                is_acknowledged=True,
                acknowledged_at=now,
                is_read=True,
                read_at=now
            )
        )
        
        await db.commit()
        return result.rowcount
    
    @staticmethod
    async def delete_notification(
        db: AsyncSession,
        notification_id: int,
        user_id: int
    ) -> bool:
        """Löscht eine spezifische Benachrichtigung"""
        from sqlalchemy import delete
        
        result = await db.execute(
            delete(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.recipient_id == user_id
                )
            )
        )
        
        await db.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def delete_all_notifications(
        db: AsyncSession,
        user_id: int
    ) -> int:
        """Löscht alle Benachrichtigungen eines Benutzers"""
        from sqlalchemy import delete
        
        result = await db.execute(
            delete(Notification).where(Notification.recipient_id == user_id)
        )
        
        await db.commit()
        return result.rowcount
    
    @staticmethod
    async def delete_old_notifications(
        db: AsyncSession,
        days_old: int = 30
    ) -> int:
        """Löscht alte Benachrichtigungen (Standard: älter als 30 Tage)"""
        from sqlalchemy import delete
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        result = await db.execute(
            delete(Notification).where(
                and_(
                    Notification.created_at < cutoff_date,
                    Notification.is_acknowledged == True
                )
            )
        )
        
        await db.commit()
        return result.rowcount
    
    @staticmethod
    async def notify_service_providers_for_new_tender(
        db: AsyncSession,
        milestone: Milestone,
        bautraeger_id: int
    ) -> List[Notification]:
        """
        Benachrichtigt Dienstleister über neue Ausschreibung basierend auf ihren Präferenzen
        
        Args:
            db: Datenbank-Session
            milestone: Das neu erstellte Milestone/Gewerk
            bautraeger_id: ID des Bauträgers, der die Ausschreibung erstellt hat
            
        Returns:
            Liste der erstellten Benachrichtigungen
        """
        from ..models.notification_preference import NotificationPreference
        from ..models.contact import Contact
        
        # Prüfe ob Milestone eine Kategorie hat
        if not milestone.category:
            return []
        
        # Finde alle aktiven Benachrichtigungspräferenzen des Bauträgers
        result = await db.execute(
            select(NotificationPreference)
            .where(
                and_(
                    NotificationPreference.user_id == bautraeger_id,
                    NotificationPreference.enabled == True
                )
            )
        )
        all_preferences = result.scalars().all()
        
        # Filtere Präferenzen nach Kategorie
        matching_preferences = []
        for pref in all_preferences:
            try:
                categories = json.loads(pref.categories) if isinstance(pref.categories, str) else pref.categories
                if milestone.category in categories:
                    matching_preferences.append(pref)
            except (json.JSONDecodeError, TypeError):
                continue
        
        # Erstelle Benachrichtigungen für jeden passenden Dienstleister
        notifications = []
        for pref in matching_preferences:
            try:
                # Hole Projekt-Informationen
                project_name = "Unbekanntes Projekt"
                if milestone.project_id:
                    project_result = await db.execute(
                        select(Project).where(Project.id == milestone.project_id)
                    )
                    project = project_result.scalar_one_or_none()
                    if project:
                        project_name = project.name
                
                # Hole Kontakt-Informationen
                contact_result = await db.execute(
                    select(Contact).where(Contact.id == pref.contact_id)
                )
                contact = contact_result.scalar_one_or_none()
                company_name = contact.company_name if contact else "Unbekannte Firma"
                
                # Erstelle Benachrichtigung
                notification = Notification(
                    recipient_id=pref.service_provider_id,
                    type=NotificationType.TENDER_INVITATION,
                    priority=NotificationPriority.MEDIUM,
                    title=f"Neue Ausschreibung: {milestone.title}",
                    message=f"Eine neue Ausschreibung in der Kategorie '{milestone.category}' wurde von {company_name} erstellt. Projekt: {project_name}",
                    data=json.dumps({
                        "milestone_id": milestone.id,
                        "milestone_title": milestone.title,
                        "project_id": milestone.project_id,
                        "project_name": project_name,
                        "category": milestone.category,
                        "bautraeger_id": bautraeger_id
                    }),
                    related_milestone_id=milestone.id,
                    related_project_id=milestone.project_id,
                    created_at=datetime.utcnow()
                )
                
                db.add(notification)
                notifications.append(notification)
                
            except Exception as e:
                print(f"Fehler beim Erstellen der Benachrichtigung fuer Dienstleister {pref.service_provider_id}: {e}")
                continue
        
        if notifications:
            await db.commit()
            print(f"=> {len(notifications)} Benachrichtigungen fuer neue Ausschreibung erstellt")
        
        return notifications
    
    @staticmethod
    async def create_acceptance_with_defects_notification(
        db: AsyncSession,
        milestone_id: int,
        service_provider_id: int,
        bautraeger_id: int
    ) -> Notification:
        """
        Erstellt eine Benachrichtigung für den Dienstleister über eine Abnahme unter Vorbehalt
        
        Args:
            db: Datenbank-Session
            milestone_id: ID des betroffenen Milestones/Gewerks
            service_provider_id: ID des Dienstleisters (Empfänger)
            bautraeger_id: ID des Bauträgers, der die Abnahme durchgeführt hat
        """
        try:
            # Lade Milestone mit Projekt-Informationen
            from ..models.milestone import Milestone
            from ..models.project import Project
            from ..models.user import User
            
            result = await db.execute(
                select(Milestone)
                .options(selectinload(Milestone.project))
                .where(Milestone.id == milestone_id)
            )
            milestone = result.scalar_one_or_none()
            
            if not milestone:
                raise ValueError(f"Milestone mit ID {milestone_id} nicht gefunden")
            
            # Lade Bauträger-Informationen
            bautraeger_result = await db.execute(
                select(User).where(User.id == bautraeger_id)
            )
            bautraeger = bautraeger_result.scalar_one_or_none()
            
            # Erstelle Bauträger Name
            bautraeger_name = "Unbekannter Bauträger"
            if bautraeger:
                if bautraeger.company_name:
                    bautraeger_name = bautraeger.company_name
                else:
                    bautraeger_name = f"{bautraeger.first_name or ''} {bautraeger.last_name or ''}".strip()
                    if not bautraeger_name:
                        bautraeger_name = f"Bauträger #{bautraeger.id}"
            
            # Projekt-Name
            project_name = milestone.project.name if milestone.project else "Unbekanntes Projekt"
            
            # Erstelle Benachrichtigungsdaten
            notification_data = {
                "milestone_id": milestone_id,
                "milestone_title": milestone.title,
                "project_id": milestone.project_id,
                "project_name": project_name,
                "bautraeger_id": bautraeger_id,
                "bautraeger_name": bautraeger_name,
                "service_provider_id": service_provider_id,
                "acceptance_type": "under_reservation",
                "defects_count": 0,  # Wird später aktualisiert wenn Mängel hinzugefügt werden
                "review_date": None,  # Wird später gesetzt wenn Review-Datum verfügbar ist
                "tradeId": milestone_id,  # Für Frontend-Kompatibilität
                "tradeTitle": milestone.title,  # Für Frontend-Kompatibilität
                "projectName": project_name  # Für Frontend-Kompatibilität
            }
            
            # Erstelle Benachrichtigung
            notification = Notification(
                recipient_id=service_provider_id,
                type=NotificationType.ACCEPTANCE_WITH_DEFECTS,
                priority=NotificationPriority.HIGH,
                title=f"Abnahme unter Vorbehalt: {milestone.title}",
                message=f"Das Gewerk '{milestone.title}' im Projekt '{project_name}' wurde von {bautraeger_name} unter Vorbehalt abgenommen. Bitte überprüfen Sie die dokumentierten Mängel und beheben Sie diese zeitnah.",
                data=json.dumps(notification_data),
                related_milestone_id=milestone_id,
                related_project_id=milestone.project_id,
                created_at=datetime.utcnow()
            )
            
            db.add(notification)
            await db.commit()
            await db.refresh(notification)
            
            print(f"[SUCCESS] Benachrichtigung für Abnahme unter Vorbehalt erstellt: Milestone {milestone_id}, Service Provider {service_provider_id}")
            return notification
            
        except Exception as e:
            print(f"[ERROR] Fehler beim Erstellen der Abnahme-unter-Vorbehalt-Benachrichtigung: {e}")
            await db.rollback()
            raise e