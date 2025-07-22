"""
Calendar Webhook Service für BuildWise
Ermöglicht automatische Synchronisation bei Kalender-Änderungen
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_

from ..models.user import User
from ..models.project import Project
from ..models.milestone import Milestone
from ..models.task import Task
from ..core.database import get_db
from ..core.config import get_settings
from .google_calendar_service import google_calendar_service
from .microsoft_calendar_service import microsoft_calendar_service

logger = logging.getLogger(__name__)
settings = get_settings()

class CalendarWebhookService:
    """Service für Kalender-Webhook Management und automatische Synchronisation"""
    
    def __init__(self):
        self.webhook_subscriptions = {}  # In-Memory Cache für aktive Subscriptions
        
    async def setup_google_webhook(self, user: User, db: AsyncSession) -> bool:
        """Richtet Google Calendar Webhook ein"""
        try:
            if not user.google_calendar_enabled or not user.google_calendar_token:
                return False
                
            credentials = await google_calendar_service.get_user_credentials(user)
            if not credentials:
                return False
                
            # Webhook-URL für Google Calendar
            webhook_url = f"{settings.base_url}/api/v1/calendar/webhook/google/{user.id}"
            
            # Channel für Notifications erstellen
            channel_data = {
                "id": f"buildwise-{user.id}-{datetime.now().timestamp()}",
                "type": "web_hook",
                "address": webhook_url,
                "token": f"buildwise-token-{user.id}",
                "expiration": int((datetime.now() + timedelta(days=7)).timestamp() * 1000)  # 7 Tage
            }
            
            # Google Calendar Watch API Call
            from googleapiclient.discovery import build
            service = build('calendar', 'v3', credentials=credentials)
            
            response = service.events().watch(
                calendarId='primary',
                body=channel_data
            ).execute()
            
            # Subscription in Datenbank speichern
            await db.execute(
                update(User)
                .where(User.id == user.id)
                .values(
                    google_webhook_channel_id=response['id'],
                    google_webhook_resource_id=response['resourceId'],
                    google_webhook_expiry=datetime.fromtimestamp(int(response['expiration']) / 1000)
                )
            )
            await db.commit()
            
            # In-Memory Cache aktualisieren
            self.webhook_subscriptions[f"google_{user.id}"] = {
                'user_id': user.id,
                'provider': 'google',
                'channel_id': response['id'],
                'resource_id': response['resourceId'],
                'expiry': datetime.fromtimestamp(int(response['expiration']) / 1000)
            }
            
            logger.info(f"✅ Google Calendar Webhook eingerichtet für User {user.id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Einrichten des Google Webhooks: {e}")
            return False
    
    async def setup_microsoft_webhook(self, user: User, db: AsyncSession) -> bool:
        """Richtet Microsoft Graph Webhook ein"""
        try:
            if not user.microsoft_calendar_enabled or not user.microsoft_calendar_token:
                return False
                
            access_token = await microsoft_calendar_service.get_access_token(user)
            if not access_token:
                return False
                
            # Webhook-URL für Microsoft Graph
            webhook_url = f"{settings.base_url}/api/v1/calendar/webhook/microsoft/{user.id}"
            
            # Subscription für Microsoft Graph erstellen
            subscription_data = {
                "changeType": "created,updated,deleted",
                "notificationUrl": webhook_url,
                "resource": "me/events",
                "expirationDateTime": (datetime.now() + timedelta(days=3)).isoformat() + "Z",  # 3 Tage (Max für Events)
                "clientState": f"buildwise-{user.id}"
            }
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://graph.microsoft.com/v1.0/subscriptions",
                    json=subscription_data,
                    headers=headers
                )
                
                if response.status_code not in [200, 201]:
                    logger.error(f"Microsoft Webhook Setup failed: {response.text}")
                    return False
                
                subscription = response.json()
                
                # Subscription in Datenbank speichern
                await db.execute(
                    update(User)
                    .where(User.id == user.id)
                    .values(
                        microsoft_webhook_subscription_id=subscription['id'],
                        microsoft_webhook_expiry=datetime.fromisoformat(subscription['expirationDateTime'].replace('Z', '+00:00'))
                    )
                )
                await db.commit()
                
                # In-Memory Cache aktualisieren
                self.webhook_subscriptions[f"microsoft_{user.id}"] = {
                    'user_id': user.id,
                    'provider': 'microsoft',
                    'subscription_id': subscription['id'],
                    'expiry': datetime.fromisoformat(subscription['expirationDateTime'].replace('Z', '+00:00'))
                }
                
                logger.info(f"✅ Microsoft Calendar Webhook eingerichtet für User {user.id}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Einrichten des Microsoft Webhooks: {e}")
            return False
    
    async def handle_google_webhook(self, user_id: int, headers: Dict[str, str], 
                                   body: bytes, db: AsyncSession) -> bool:
        """Verarbeitet Google Calendar Webhook Notifications"""
        try:
            # Validiere Webhook
            channel_id = headers.get('x-goog-channel-id')
            resource_state = headers.get('x-goog-resource-state')
            
            if not channel_id or resource_state not in ['exists', 'sync']:
                return False
                
            # Lade User
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user or not user.google_calendar_enabled:
                return False
                
            logger.info(f"📅 Google Calendar Webhook empfangen für User {user_id}: {resource_state}")
            
            # Synchronisiere Kalender-Events
            await self._sync_calendar_changes(user, 'google', db)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Verarbeiten des Google Webhooks: {e}")
            return False
    
    async def handle_microsoft_webhook(self, user_id: int, notification_data: Dict[str, Any], 
                                     db: AsyncSession) -> bool:
        """Verarbeitet Microsoft Graph Webhook Notifications"""
        try:
            # Validiere Notification
            if not notification_data.get('value'):
                return False
                
            # Lade User
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user or not user.microsoft_calendar_enabled:
                return False
                
            logger.info(f"📅 Microsoft Calendar Webhook empfangen für User {user_id}")
            
            # Verarbeite jede Notification
            for notification in notification_data['value']:
                change_type = notification.get('changeType')
                resource = notification.get('resource')
                
                logger.info(f"📝 Change: {change_type} für Resource: {resource}")
                
                # Synchronisiere basierend auf Change Type
                if change_type in ['created', 'updated', 'deleted']:
                    await self._sync_calendar_changes(user, 'microsoft', db)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Verarbeiten des Microsoft Webhooks: {e}")
            return False
    
    async def _sync_calendar_changes(self, user: User, provider: str, db: AsyncSession):
        """Synchronisiert Kalender-Änderungen mit BuildWise Daten"""
        try:
            # Lade alle Projekte des Users
            projects_result = await db.execute(
                select(Project).where(Project.created_by == user.id)
            )
            projects = projects_result.scalars().all()
            
            # Lade Events vom Kalender-Provider
            if provider == 'google':
                calendar_events = await self._get_google_events(user)
            elif provider == 'microsoft':
                calendar_events = await self._get_microsoft_events(user)
            else:
                return
                
            # Analysiere Events und erkenne BuildWise-bezogene Termine
            buildwise_events = []
            for event in calendar_events:
                if self._is_buildwise_event(event):
                    buildwise_events.append(event)
            
            # Synchronisiere erkannte Events mit Meilensteinen/Tasks
            for event in buildwise_events:
                await self._sync_event_with_buildwise(event, user, projects, db)
                
            logger.info(f"✅ {len(buildwise_events)} BuildWise Events synchronisiert für User {user.id}")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Kalender-Synchronisation: {e}")
    
    async def _get_google_events(self, user: User) -> List[Dict[str, Any]]:
        """Lädt aktuelle Events von Google Calendar"""
        try:
            credentials = await google_calendar_service.get_user_credentials(user)
            if not credentials:
                return []
                
            from googleapiclient.discovery import build
            service = build('calendar', 'v3', credentials=credentials)
            
            # Events der letzten 30 Tage und nächsten 90 Tage
            time_min = (datetime.now() - timedelta(days=30)).isoformat() + 'Z'
            time_max = (datetime.now() + timedelta(days=90)).isoformat() + 'Z'
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=100,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Konvertiere zu standardisiertem Format
            standardized_events = []
            for event in events:
                standardized_events.append({
                    'id': event.get('id'),
                    'title': event.get('summary', ''),
                    'description': event.get('description', ''),
                    'start': event.get('start', {}).get('dateTime', event.get('start', {}).get('date')),
                    'end': event.get('end', {}).get('dateTime', event.get('end', {}).get('date')),
                    'location': event.get('location', ''),
                    'provider': 'google'
                })
            
            return standardized_events
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Google Events: {e}")
            return []
    
    async def _get_microsoft_events(self, user: User) -> List[Dict[str, Any]]:
        """Lädt aktuelle Events von Microsoft Calendar"""
        try:
            access_token = await microsoft_calendar_service.get_access_token(user)
            if not access_token:
                return []
                
            # Events der letzten 30 Tage und nächsten 90 Tage
            start_time = (datetime.now() - timedelta(days=30)).isoformat()
            end_time = (datetime.now() + timedelta(days=90)).isoformat()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            params = {
                'startDateTime': start_time,
                'endDateTime': end_time,
                '$select': 'id,subject,body,start,end,location',
                '$orderby': 'start/dateTime',
                '$top': 100
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://graph.microsoft.com/v1.0/me/calendarview",
                    params=params,
                    headers=headers
                )
                
                if response.status_code != 200:
                    logger.error(f"Microsoft Events laden fehlgeschlagen: {response.text}")
                    return []
                
                events_data = response.json()
                events = events_data.get('value', [])
                
                # Konvertiere zu standardisiertem Format
                standardized_events = []
                for event in events:
                    standardized_events.append({
                        'id': event.get('id'),
                        'title': event.get('subject', ''),
                        'description': event.get('body', {}).get('content', ''),
                        'start': event.get('start', {}).get('dateTime'),
                        'end': event.get('end', {}).get('dateTime'),
                        'location': event.get('location', {}).get('displayName', ''),
                        'provider': 'microsoft'
                    })
                
                return standardized_events
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Microsoft Events: {e}")
            return []
    
    def _is_buildwise_event(self, event: Dict[str, Any]) -> bool:
        """Prüft ob ein Event BuildWise-bezogen ist"""
        title = event.get('title', '').lower()
        description = event.get('description', '').lower()
        
        # BuildWise Keywords
        buildwise_keywords = [
            'buildwise',
            'meilenstein',
            'milestone',
            'bauphase',
            'projekt',
            'gewerk',
            'baustelle',
            'bauträger'
        ]
        
        # Prüfe Titel und Beschreibung
        for keyword in buildwise_keywords:
            if keyword in title or keyword in description:
                return True
                
        # Prüfe auf BuildWise Icons/Emojis
        buildwise_icons = ['📋', '✅', '🏗️', '🤝', '📅']
        for icon in buildwise_icons:
            if icon in title or icon in description:
                return True
                
        return False
    
    async def _sync_event_with_buildwise(self, event: Dict[str, Any], user: User, 
                                       projects: List[Project], db: AsyncSession):
        """Synchronisiert ein Event mit BuildWise Meilensteinen/Tasks"""
        try:
            title = event.get('title', '')
            description = event.get('description', '')
            
            # Versuche Projekt zu identifizieren
            identified_project = None
            for project in projects:
                if project.name.lower() in title.lower() or project.name.lower() in description.lower():
                    identified_project = project
                    break
            
            if not identified_project and projects:
                # Fallback: Nehme das neueste Projekt
                identified_project = max(projects, key=lambda p: p.created_at)
            
            if not identified_project:
                return
                
            # Prüfe ob es ein Meilenstein oder Task ist
            if '📋' in title or 'meilenstein' in title.lower():
                await self._sync_as_milestone(event, identified_project, user, db)
            elif '✅' in title or 'aufgabe' in title.lower() or 'task' in title.lower():
                await self._sync_as_task(event, identified_project, user, db)
            else:
                # Erstelle als allgemeines Projekt-Event
                await self._create_project_event(event, identified_project, user, db)
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Event-Synchronisation: {e}")
    
    async def _sync_as_milestone(self, event: Dict[str, Any], project: Project, 
                               user: User, db: AsyncSession):
        """Synchronisiert Event als Meilenstein"""
        try:
            # Prüfe ob Meilenstein bereits existiert
            existing_milestone = await db.execute(
                select(Milestone).where(
                    and_(
                        Milestone.project_id == project.id,
                        Milestone.title.ilike(f"%{event.get('title', '').replace('📋', '').strip()}%")
                    )
                )
            )
            milestone = existing_milestone.scalar_one_or_none()
            
            if not milestone:
                # Erstelle neuen Meilenstein
                start_date = datetime.fromisoformat(event.get('start', '').replace('Z', '+00:00')).date()
                
                new_milestone = Milestone(
                    project_id=project.id,
                    created_by=user.id,
                    title=event.get('title', '').replace('📋', '').strip(),
                    description=f"Automatisch synchronisiert aus {event.get('provider')} Calendar\n\n{event.get('description', '')}",
                    planned_date=start_date,
                    status='PLANNED',
                    priority='MEDIUM'
                )
                
                db.add(new_milestone)
                await db.commit()
                
                logger.info(f"✅ Meilenstein '{new_milestone.title}' automatisch erstellt")
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Meilenstein-Synchronisation: {e}")
    
    async def _sync_as_task(self, event: Dict[str, Any], project: Project, 
                          user: User, db: AsyncSession):
        """Synchronisiert Event als Task"""
        try:
            # Prüfe ob Task bereits existiert
            existing_task = await db.execute(
                select(Task).where(
                    and_(
                        Task.project_id == project.id,
                        Task.title.ilike(f"%{event.get('title', '').replace('✅', '').strip()}%")
                    )
                )
            )
            task = existing_task.scalar_one_or_none()
            
            if not task:
                # Erstelle neue Aufgabe
                due_date = datetime.fromisoformat(event.get('start', '').replace('Z', '+00:00')).date()
                
                new_task = Task(
                    project_id=project.id,
                    created_by=user.id,
                    title=event.get('title', '').replace('✅', '').strip(),
                    description=f"Automatisch synchronisiert aus {event.get('provider')} Calendar\n\n{event.get('description', '')}",
                    due_date=due_date,
                    status='TODO',
                    priority='MEDIUM'
                )
                
                db.add(new_task)
                await db.commit()
                
                logger.info(f"✅ Task '{new_task.title}' automatisch erstellt")
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Task-Synchronisation: {e}")
    
    async def _create_project_event(self, event: Dict[str, Any], project: Project, 
                                  user: User, db: AsyncSession):
        """Erstellt allgemeines Projekt-Event (falls nötig)"""
        try:
            # Hier könnte eine Event-Tabelle erstellt werden für allgemeine Projekt-Events
            # Für jetzt loggen wir nur
            logger.info(f"📅 Projekt-Event erkannt: '{event.get('title')}' für Projekt '{project.name}'")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Projekt-Event-Erstellung: {e}")
    
    async def renew_expiring_webhooks(self, db: AsyncSession):
        """Erneuert ablaufende Webhook-Subscriptions"""
        try:
            # Finde Users mit ablaufenden Webhooks (nächste 24 Stunden)
            tomorrow = datetime.now() + timedelta(hours=24)
            
            # Google Webhooks
            google_users = await db.execute(
                select(User).where(
                    and_(
                        User.google_calendar_enabled == True,
                        User.google_webhook_expiry < tomorrow,
                        User.google_webhook_expiry.isnot(None)
                    )
                )
            )
            
            for user in google_users.scalars():
                await self.setup_google_webhook(user, db)
                logger.info(f"🔄 Google Webhook erneuert für User {user.id}")
            
            # Microsoft Webhooks
            microsoft_users = await db.execute(
                select(User).where(
                    and_(
                        User.microsoft_calendar_enabled == True,
                        User.microsoft_webhook_expiry < tomorrow,
                        User.microsoft_webhook_expiry.isnot(None)
                    )
                )
            )
            
            for user in microsoft_users.scalars():
                await self.setup_microsoft_webhook(user, db)
                logger.info(f"🔄 Microsoft Webhook erneuert für User {user.id}")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Erneuern der Webhooks: {e}")
    
    async def cleanup_expired_webhooks(self, db: AsyncSession):
        """Räumt abgelaufene Webhook-Subscriptions auf"""
        try:
            now = datetime.now()
            
            # Cleanup Google Webhooks
            await db.execute(
                update(User)
                .where(User.google_webhook_expiry < now)
                .values(
                    google_webhook_channel_id=None,
                    google_webhook_resource_id=None,
                    google_webhook_expiry=None
                )
            )
            
            # Cleanup Microsoft Webhooks
            await db.execute(
                update(User)
                .where(User.microsoft_webhook_expiry < now)
                .values(
                    microsoft_webhook_subscription_id=None,
                    microsoft_webhook_expiry=None
                )
            )
            
            await db.commit()
            logger.info("🧹 Abgelaufene Webhooks bereinigt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Bereinigen der Webhooks: {e}")


# Globale Service-Instanz
calendar_webhook_service = CalendarWebhookService() 