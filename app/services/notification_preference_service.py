"""
Notification Preference Service
Business Logic für Benachrichtigungspräferenzen
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import json
from datetime import datetime

from app.models.notification_preference import NotificationPreference
from app.models.contact import Contact
from app.schemas.notification_preference import (
    NotificationPreferenceCreate,
    NotificationPreferenceUpdate
)


class NotificationPreferenceService:
    """Service für Benachrichtigungspräferenzen"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def upsert_preference(
        self,
        data: NotificationPreferenceCreate,
        current_user_id: int
    ) -> NotificationPreference:
        """
        Erstellt oder aktualisiert eine Benachrichtigungspräferenz
        
        Args:
            data: Daten für die Präferenz
            current_user_id: ID des aktuellen Users (Bauträger)
            
        Returns:
            Erstellte oder aktualisierte Präferenz
        """
        # Prüfe ob Kontakt existiert und dem User gehört
        result = await self.db.execute(
            select(Contact).where(
                Contact.id == data.contact_id,
                Contact.user_id == current_user_id
            )
        )
        contact = result.scalar_one_or_none()
        
        if not contact:
            raise ValueError("Kontakt nicht gefunden oder keine Berechtigung")
        
        # Konvertiere Categories zu JSON
        categories_json = json.dumps(data.categories)
        
        # Prüfe ob Präferenz bereits existiert
        result = await self.db.execute(
            select(NotificationPreference).where(
                NotificationPreference.contact_id == data.contact_id
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update
            existing.enabled = data.enabled
            existing.categories = categories_json
            existing.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            # Create
            preference = NotificationPreference(
                contact_id=data.contact_id,
                user_id=current_user_id,
                service_provider_id=data.service_provider_id,
                enabled=data.enabled,
                categories=categories_json
            )
            self.db.add(preference)
            await self.db.commit()
            await self.db.refresh(preference)
            return preference
    
    async def get_by_contact_id(
        self,
        contact_id: int,
        current_user_id: int
    ) -> Optional[NotificationPreference]:
        """
        Holt Benachrichtigungspräferenz für einen Kontakt
        
        Args:
            contact_id: ID des Kontakts
            current_user_id: ID des aktuellen Users
            
        Returns:
            Präferenz oder None
        """
        # Prüfe ob Kontakt dem User gehört
        result = await self.db.execute(
            select(Contact).where(
                Contact.id == contact_id,
                Contact.user_id == current_user_id
            )
        )
        contact = result.scalar_one_or_none()
        
        if not contact:
            return None
        
        result = await self.db.execute(
            select(NotificationPreference).where(
                NotificationPreference.contact_id == contact_id
            )
        )
        return result.scalar_one_or_none()
    
    async def toggle(
        self,
        preference_id: int,
        enabled: bool,
        current_user_id: int
    ) -> NotificationPreference:
        """
        Schaltet Benachrichtigungen an/aus
        
        Args:
            preference_id: ID der Präferenz
            enabled: Neuer Status
            current_user_id: ID des aktuellen Users
            
        Returns:
            Aktualisierte Präferenz
        """
        result = await self.db.execute(
            select(NotificationPreference).where(
                NotificationPreference.id == preference_id,
                NotificationPreference.user_id == current_user_id
            )
        )
        preference = result.scalar_one_or_none()
        
        if not preference:
            raise ValueError("Präferenz nicht gefunden oder keine Berechtigung")
        
        preference.enabled = enabled
        preference.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(preference)
        
        return preference
    
    async def update_categories(
        self,
        preference_id: int,
        categories: List[str],
        current_user_id: int
    ) -> NotificationPreference:
        """
        Aktualisiert die Kategorien einer Präferenz
        
        Args:
            preference_id: ID der Präferenz
            categories: Neue Liste der Kategorien
            current_user_id: ID des aktuellen Users
            
        Returns:
            Aktualisierte Präferenz
        """
        result = await self.db.execute(
            select(NotificationPreference).where(
                NotificationPreference.id == preference_id,
                NotificationPreference.user_id == current_user_id
            )
        )
        preference = result.scalar_one_or_none()
        
        if not preference:
            raise ValueError("Präferenz nicht gefunden oder keine Berechtigung")
        
        preference.categories = json.dumps(categories)
        preference.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(preference)
        
        return preference
    
    async def delete(
        self,
        preference_id: int,
        current_user_id: int
    ) -> None:
        """
        Löscht eine Benachrichtigungspräferenz
        
        Args:
            preference_id: ID der Präferenz
            current_user_id: ID des aktuellen Users
        """
        result = await self.db.execute(
            select(NotificationPreference).where(
                NotificationPreference.id == preference_id,
                NotificationPreference.user_id == current_user_id
            )
        )
        preference = result.scalar_one_or_none()
        
        if not preference:
            raise ValueError("Präferenz nicht gefunden oder keine Berechtigung")
        
        await self.db.execute(
            delete(NotificationPreference).where(NotificationPreference.id == preference_id)
        )
        await self.db.commit()
    
    async def get_active_preferences_for_category(
        self,
        category: str,
        bautraeger_user_id: int
    ) -> List[NotificationPreference]:
        """
        Holt alle aktiven Präferenzen für eine bestimmte Kategorie
        Wird verwendet um Dienstleister zu benachrichtigen wenn eine Ausschreibung erstellt wird
        
        Args:
            category: Kategorie (z.B. 'electrical', 'plumbing')
            bautraeger_user_id: ID des Bauträgers der die Ausschreibung erstellt
            
        Returns:
            Liste der aktiven Präferenzen
        """
        result = await self.db.execute(
            select(NotificationPreference).where(
                NotificationPreference.enabled == True,
                NotificationPreference.user_id == bautraeger_user_id
            )
        )
        all_preferences = result.scalars().all()
        
        # Filtere nach Kategorie (JSON-Suche)
        matching_preferences = []
        for pref in all_preferences:
            try:
                categories = json.loads(pref.categories)
                if category in categories:
                    matching_preferences.append(pref)
            except (json.JSONDecodeError, TypeError):
                continue
        
        return matching_preferences

