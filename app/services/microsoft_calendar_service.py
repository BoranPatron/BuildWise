"""
Microsoft Outlook Calendar API Service für BuildWise
Ermöglicht Outlook/Exchange Kalender-Integration und E-Mail-Funktionen
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx
import json
import logging
from urllib.parse import urlencode

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from ..models.user import User
from ..models.milestone import Milestone
from ..models.project import Project
from ..models.task import Task
from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class MicrosoftCalendarService:
    """Service für Microsoft Outlook Calendar Integration"""
    
    # OAuth 2.0 Scopes für Microsoft Graph
    SCOPES = [
        'https://graph.microsoft.com/Calendars.ReadWrite',
        'https://graph.microsoft.com/Calendars.ReadWrite.Shared',
        'https://graph.microsoft.com/Mail.Send',
        'https://graph.microsoft.com/Mail.Read',
        'https://graph.microsoft.com/User.Read'
    ]
    
    def __init__(self):
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"
        self.auth_endpoint = "https://login.microsoftonline.com/common/oauth2/v2.0"
        
    async def get_authorization_url(self, user_id: int) -> str:
        """Generiert OAuth2 Authorization URL für Microsoft Graph"""
        try:
            params = {
                'client_id': settings.microsoft_client_id,
                'response_type': 'code',
                'redirect_uri': f"{settings.base_url}/api/v1/calendar/microsoft/callback",
                'scope': ' '.join(self.SCOPES),
                'response_mode': 'query',
                'state': str(user_id)
            }
            
            authorization_url = f"{self.auth_endpoint}/authorize?{urlencode(params)}"
            return authorization_url
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der Microsoft Authorization URL: {e}")
            raise
    
    async def handle_oauth_callback(self, code: str, state: str, db: AsyncSession) -> Dict[str, Any]:
        """Verarbeitet OAuth2 Callback und speichert Credentials"""
        try:
            user_id = int(state)
            
            # Exchange code for token
            token_data = {
                'client_id': settings.microsoft_client_id,
                'client_secret': settings.microsoft_client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': f"{settings.base_url}/api/v1/calendar/microsoft/callback",
                'scope': ' '.join(self.SCOPES)
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.auth_endpoint}/token",
                    data=token_data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                
                if response.status_code != 200:
                    raise Exception(f"Token exchange failed: {response.text}")
                
                token_info = response.json()
            
            # Speichere Credentials in der Datenbank
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    microsoft_calendar_token=token_info['access_token'],
                    microsoft_calendar_refresh_token=token_info.get('refresh_token'),
                    microsoft_calendar_token_expiry=datetime.now() + timedelta(seconds=token_info['expires_in']),
                    microsoft_calendar_enabled=True
                )
            )
            await db.commit()
            
            logger.info(f"✅ Microsoft Calendar erfolgreich für User {user_id} aktiviert")
            
            return {
                "success": True,
                "message": "Microsoft Calendar erfolgreich verbunden",
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Microsoft OAuth Callback: {e}")
            raise
    
    async def get_access_token(self, user: User) -> Optional[str]:
        """Lädt und refresht Access Token"""
        if not user.microsoft_calendar_enabled or not user.microsoft_calendar_token:
            return None
            
        try:
            # Prüfe Token-Gültigkeit
            if user.microsoft_calendar_token_expiry and user.microsoft_calendar_token_expiry > datetime.now():
                return user.microsoft_calendar_token
            
            # Refresh token if expired
            if user.microsoft_calendar_refresh_token:
                return await self._refresh_access_token(user)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Access Tokens: {e}")
            return None
    
    async def _refresh_access_token(self, user: User) -> Optional[str]:
        """Refresht den Access Token"""
        try:
            refresh_data = {
                'client_id': settings.microsoft_client_id,
                'client_secret': settings.microsoft_client_secret,
                'refresh_token': user.microsoft_calendar_refresh_token,
                'grant_type': 'refresh_token',
                'scope': ' '.join(self.SCOPES)
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.auth_endpoint}/token",
                    data=refresh_data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                
                if response.status_code != 200:
                    logger.error(f"Token refresh failed: {response.text}")
                    return None
                
                token_info = response.json()
                
                # Update token in database (would need async context)
                # This is simplified - in real implementation, we'd need to handle this properly
                
                return token_info['access_token']
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Token Refresh: {e}")
            return None
    
    async def create_calendar_event(self, user: User, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Erstellt ein Event im Outlook Calendar"""
        access_token = await self.get_access_token(user)
        if not access_token:
            return None
            
        try:
            # Event-Daten für Microsoft Graph formatieren
            event = {
                "subject": event_data.get('title', 'BuildWise Event'),
                "body": {
                    "contentType": "HTML",
                    "content": event_data.get('description', '').replace('\n', '<br>')
                },
                "start": {
                    "dateTime": event_data['start_time'].isoformat(),
                    "timeZone": event_data.get('timezone', 'Europe/Zurich')
                },
                "end": {
                    "dateTime": event_data['end_time'].isoformat(),
                    "timeZone": event_data.get('timezone', 'Europe/Zurich')
                },
                "location": {
                    "displayName": event_data.get('location', '')
                },
                "attendees": [
                    {
                        "emailAddress": {"address": email, "name": email.split('@')[0]},
                        "type": "required"
                    } for email in event_data.get('attendees', [])
                ],
                "reminderMinutesBeforeStart": 30,
                "isReminderOn": True
            }
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.graph_endpoint}/me/events",
                    json=event,
                    headers=headers
                )
                
                if response.status_code not in [200, 201]:
                    logger.error(f"Event creation failed: {response.text}")
                    return None
                
                created_event = response.json()
                
                logger.info(f"✅ Outlook Calendar Event erstellt: {created_event['id']}")
                
                return {
                    'event_id': created_event['id'],
                    'web_link': created_event.get('webLink'),
                    'status': 'created'
                }
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des Outlook Events: {e}")
            return None
    
    async def sync_milestone_to_calendar(self, user: User, milestone: Milestone, db: AsyncSession) -> bool:
        """Synchronisiert einen Meilenstein mit Outlook Calendar"""
        try:
            # Lade Projekt-Details
            project_result = await db.execute(
                select(Project).where(Project.id == milestone.project_id)
            )
            project = project_result.scalar_one_or_none()
            
            if not project:
                return False
            
            # Event-Daten zusammenstellen
            event_data = {
                'title': f"📋 {milestone.title} - {project.name}",
                'description': f"""
<h3>🏗️ BuildWise Meilenstein</h3>

<p><strong>Projekt:</strong> {project.name}</p>
<p><strong>Meilenstein:</strong> {milestone.title}</p>
<p><strong>Status:</strong> {milestone.status.value}</p>
<p><strong>Priorität:</strong> {milestone.priority.value}</p>

<p>{milestone.description or ''}</p>

<p><a href="{settings.base_url}/projects/{project.id}">🔗 BuildWise öffnen</a></p>
                """.strip(),
                'start_time': datetime.combine(milestone.planned_date, datetime.min.time()),
                'end_time': datetime.combine(milestone.planned_date, datetime.min.time()) + timedelta(hours=1),
                'location': project.address or '',
                'attendees': [],
            }
            
            result = await self.create_calendar_event(user, event_data)
            return result is not None
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Synchronisieren des Meilensteins: {e}")
            return False
    
    async def sync_task_to_calendar(self, user: User, task: Task, db: AsyncSession) -> bool:
        """Synchronisiert eine Aufgabe mit Outlook Calendar"""
        try:
            if not task.due_date:
                return False
                
            # Lade Projekt-Details
            project_result = await db.execute(
                select(Project).where(Project.id == task.project_id)
            )
            project = project_result.scalar_one_or_none()
            
            if not project:
                return False
            
            # Event-Daten zusammenstellen
            event_data = {
                'title': f"✅ {task.title} - {project.name}",
                'description': f"""
<h3>🏗️ BuildWise Aufgabe</h3>

<p><strong>Projekt:</strong> {project.name}</p>
<p><strong>Aufgabe:</strong> {task.title}</p>
<p><strong>Status:</strong> {task.status.value}</p>
<p><strong>Priorität:</strong> {task.priority.value}</p>
<p><strong>Fortschritt:</strong> {task.progress_percentage}%</p>

<p>{task.description or ''}</p>

<p><a href="{settings.base_url}/projects/{project.id}/tasks/{task.id}">🔗 BuildWise öffnen</a></p>
                """.strip(),
                'start_time': datetime.combine(task.due_date, datetime.min.time()),
                'end_time': datetime.combine(task.due_date, datetime.min.time()) + timedelta(hours=2),
                'location': project.address or '',
                'attendees': [],
            }
            
            result = await self.create_calendar_event(user, event_data)
            return result is not None
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Synchronisieren der Aufgabe: {e}")
            return False
    
    async def send_project_update_email(self, user: User, project: Project, recipients: List[str], 
                                       subject: str, content: str) -> bool:
        """Sendet Projekt-Update E-Mail über Outlook"""
        access_token = await self.get_access_token(user)
        if not access_token:
            return False
            
        try:
            # E-Mail zusammenstellen
            email_message = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "HTML",
                        "content": f"""
<h2>📧 BuildWise Projekt-Update</h2>

<p><strong>Projekt:</strong> {project.name}</p>

<div style="margin: 20px 0;">
{content.replace('\n', '<br>')}
</div>

<hr>
<p><small>Diese E-Mail wurde über BuildWise gesendet.</small></p>
<p><a href="{settings.base_url}/projects/{project.id}">🔗 Projekt in BuildWise öffnen</a></p>
                        """
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": email,
                                "name": email.split('@')[0]
                            }
                        } for email in recipients
                    ]
                },
                "saveToSentItems": "true"
            }
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.graph_endpoint}/me/sendMail",
                    json=email_message,
                    headers=headers
                )
                
                if response.status_code not in [200, 202]:
                    logger.error(f"Email sending failed: {response.text}")
                    return False
                
                logger.info(f"✅ Projekt-Update E-Mail gesendet für Projekt {project.id}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Senden der E-Mail: {e}")
            return False
    
    async def create_meeting_invitation(self, user: User, meeting_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Erstellt eine Meeting-Einladung in Outlook"""
        try:
            # Erweiterte Event-Daten für Meetings
            event_data = {
                'title': f"🤝 {meeting_data.get('title', 'BuildWise Meeting')}",
                'description': f"""
<h3>🏗️ BuildWise Meeting</h3>

<p>{meeting_data.get('description', '')}</p>

<h4>📋 Agenda:</h4>
<p>{meeting_data.get('agenda', 'Keine Agenda angegeben')}</p>

<p><a href="{settings.base_url}">🔗 BuildWise öffnen</a></p>
                """.strip(),
                'start_time': meeting_data['start_time'],
                'end_time': meeting_data['end_time'],
                'location': meeting_data.get('location', 'Online'),
                'attendees': meeting_data.get('attendees', []),
            }
            
            result = await self.create_calendar_event(user, event_data)
            
            if result:
                # Optional: Teams Meeting hinzufügen
                await self._add_teams_meeting(user, result['event_id'], meeting_data)
                
            return result
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der Meeting-Einladung: {e}")
            return None
    
    async def _add_teams_meeting(self, user: User, event_id: str, meeting_data: Dict[str, Any]):
        """Fügt Teams Meeting zu einem Event hinzu"""
        access_token = await self.get_access_token(user)
        if not access_token:
            return
            
        try:
            # Teams Meeting hinzufügen
            teams_meeting = {
                "isOnlineMeeting": True,
                "onlineMeetingProvider": "teamsForBusiness"
            }
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.graph_endpoint}/me/events/{event_id}",
                    json=teams_meeting,
                    headers=headers
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Teams Meeting zu Event {event_id} hinzugefügt")
                else:
                    logger.warning(f"⚠️ Teams Meeting konnte nicht hinzugefügt werden: {response.text}")
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Hinzufügen des Teams Meetings: {e}")
    
    async def get_calendar_availability(self, user: User, start_time: datetime, 
                                      end_time: datetime) -> Dict[str, Any]:
        """Prüft Verfügbarkeit im Outlook Calendar"""
        access_token = await self.get_access_token(user)
        if not access_token:
            return {"available": False, "reason": "No calendar access"}
            
        try:
            # FreeBusy Query
            freebusy_query = {
                "schedules": [user.email],
                "startTime": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": "Europe/Zurich"
                },
                "endTime": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": "Europe/Zurich"
                },
                "availabilityViewInterval": 60
            }
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.graph_endpoint}/me/calendar/getSchedule",
                    json=freebusy_query,
                    headers=headers
                )
                
                if response.status_code != 200:
                    return {"available": False, "reason": "API error"}
                
                schedule_data = response.json()
                busy_times = schedule_data.get('value', [{}])[0].get('busyViewTimes', [])
                
                is_available = len(busy_times) == 0
                
                return {
                    "available": is_available,
                    "busy_times": busy_times,
                    "suggested_times": await self._suggest_alternative_times(user, start_time, end_time) if not is_available else []
                }
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Prüfen der Verfügbarkeit: {e}")
            return {"available": False, "reason": str(e)}
    
    async def _suggest_alternative_times(self, user: User, original_start: datetime, 
                                       original_end: datetime) -> List[Dict[str, Any]]:
        """Schlägt alternative Meeting-Zeiten vor"""
        try:
            suggestions = []
            duration = original_end - original_start
            
            # Suche nach freien Zeiten in den nächsten 7 Tagen
            for day_offset in range(1, 8):
                check_date = original_start + timedelta(days=day_offset)
                
                # Prüfe verschiedene Uhrzeiten (Geschäftszeiten)
                for hour in [9, 10, 11, 14, 15, 16]:
                    suggested_start = check_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                    suggested_end = suggested_start + duration
                    
                    # Prüfe Verfügbarkeit für diesen Zeitslot
                    availability = await self.get_calendar_availability(user, suggested_start, suggested_end)
                    
                    if availability.get('available'):
                        suggestions.append({
                            "start": suggested_start.isoformat(),
                            "end": suggested_end.isoformat(),
                            "date": suggested_start.strftime("%A, %d.%m.%Y"),
                            "time": f"{suggested_start.strftime('%H:%M')} - {suggested_end.strftime('%H:%M')}"
                        })
                        
                        if len(suggestions) >= 3:
                            break
                
                if len(suggestions) >= 3:
                    break
            
            return suggestions[:3]  # Maximal 3 Vorschläge
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen von Zeitvorschlägen: {e}")
            return []
    
    async def get_calendar_events(self, user: User, start_date: datetime, 
                                 end_date: datetime) -> List[Dict[str, Any]]:
        """Lädt Events aus dem Outlook Calendar"""
        access_token = await self.get_access_token(user)
        if not access_token:
            return []
            
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            params = {
                'startDateTime': start_date.isoformat(),
                'endDateTime': end_date.isoformat(),
                '$select': 'subject,start,end,location,attendees,organizer,webLink',
                '$orderby': 'start/dateTime'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.graph_endpoint}/me/calendarview",
                    params=params,
                    headers=headers
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to fetch calendar events: {response.text}")
                    return []
                
                events_data = response.json()
                events = []
                
                for event in events_data.get('value', []):
                    events.append({
                        'id': event.get('id'),
                        'title': event.get('subject', 'Kein Titel'),
                        'start': event.get('start', {}).get('dateTime'),
                        'end': event.get('end', {}).get('dateTime'),
                        'location': event.get('location', {}).get('displayName', ''),
                        'attendees_count': len(event.get('attendees', [])),
                        'web_link': event.get('webLink')
                    })
                
                return events
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Kalender-Events: {e}")
            return []


# Globale Service-Instanz
microsoft_calendar_service = MicrosoftCalendarService() 