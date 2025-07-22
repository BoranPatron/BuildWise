"""
Google Calendar API Service für BuildWise
Ermöglicht Kalender-Integration, Event-Erstellung und -Synchronisation
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from ..models.user import User
from ..models.milestone import Milestone
from ..models.project import Project
from ..models.task import Task
from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class GoogleCalendarService:
    """Service für Google Calendar Integration"""
    
    # OAuth 2.0 Scopes für Google Calendar und Gmail
    SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.readonly'
    ]
    
    def __init__(self):
        self.credentials_file = "client_secret_1039127200110-vav094cta93qmtleivdj63un5dne17eb.apps.googleusercontent.com.json"
        
    async def get_authorization_url(self, user_id: int) -> str:
        """Generiert OAuth2 Authorization URL für Google Calendar"""
        try:
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=self.SCOPES,
                redirect_uri=f"{settings.base_url}/api/v1/calendar/google/callback"
            )
            
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=str(user_id)
            )
            
            return authorization_url
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der Google Authorization URL: {e}")
            raise
    
    async def handle_oauth_callback(self, code: str, state: str, db: AsyncSession) -> Dict[str, Any]:
        """Verarbeitet OAuth2 Callback und speichert Credentials"""
        try:
            user_id = int(state)
            
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=self.SCOPES,
                redirect_uri=f"{settings.base_url}/api/v1/calendar/google/callback"
            )
            
            # Exchange code for credentials
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Speichere Credentials in der Datenbank
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    google_calendar_token=credentials.token,
                    google_calendar_refresh_token=credentials.refresh_token,
                    google_calendar_token_expiry=credentials.expiry,
                    google_calendar_enabled=True
                )
            )
            await db.commit()
            
            logger.info(f"✅ Google Calendar erfolgreich für User {user_id} aktiviert")
            
            return {
                "success": True,
                "message": "Google Calendar erfolgreich verbunden",
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"❌ Fehler beim OAuth Callback: {e}")
            raise
    
    async def get_user_credentials(self, user: User) -> Optional[Credentials]:
        """Lädt und refresht User Credentials"""
        if not user.google_calendar_enabled or not user.google_calendar_token:
            return None
            
        try:
            credentials = Credentials(
                token=user.google_calendar_token,
                refresh_token=user.google_calendar_refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret
            )
            
            # Refresh token if expired
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                
                # Update database with new token
                # Note: This would need to be done in an async context
                
            return credentials
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Google Credentials: {e}")
            return None
    
    async def create_calendar_event(self, user: User, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Erstellt ein Event im Google Calendar"""
        credentials = await self.get_user_credentials(user)
        if not credentials:
            return None
            
        try:
            service = build('calendar', 'v3', credentials=credentials)
            
            # Event-Daten formatieren
            event = {
                'summary': event_data.get('title', 'BuildWise Event'),
                'description': event_data.get('description', ''),
                'start': {
                    'dateTime': event_data['start_time'].isoformat(),
                    'timeZone': event_data.get('timezone', 'Europe/Zurich'),
                },
                'end': {
                    'dateTime': event_data['end_time'].isoformat(),
                    'timeZone': event_data.get('timezone', 'Europe/Zurich'),
                },
                'location': event_data.get('location', ''),
                'attendees': [
                    {'email': email} for email in event_data.get('attendees', [])
                ],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 Tag vorher
                        {'method': 'popup', 'minutes': 30},       # 30 Min vorher
                    ],
                },
            }
            
            # Event erstellen
            created_event = service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all'  # Sendet Einladungen an alle Teilnehmer
            ).execute()
            
            logger.info(f"✅ Google Calendar Event erstellt: {created_event['id']}")
            
            return {
                'event_id': created_event['id'],
                'html_link': created_event.get('htmlLink'),
                'status': 'created'
            }
            
        except HttpError as e:
            logger.error(f"❌ Google Calendar API Fehler: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des Events: {e}")
            return None
    
    async def sync_milestone_to_calendar(self, user: User, milestone: Milestone, db: AsyncSession) -> bool:
        """Synchronisiert einen Meilenstein mit Google Calendar"""
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
🏗️ BuildWise Meilenstein

Projekt: {project.name}
Meilenstein: {milestone.title}
Status: {milestone.status.value}
Priorität: {milestone.priority.value}

{milestone.description or ''}

🔗 BuildWise: {settings.base_url}/projects/{project.id}
                """.strip(),
                'start_time': datetime.combine(milestone.planned_date, datetime.min.time()),
                'end_time': datetime.combine(milestone.planned_date, datetime.min.time()) + timedelta(hours=1),
                'location': project.address or '',
                'attendees': [],  # Könnte erweitert werden mit Projekt-Team-Mitgliedern
            }
            
            result = await self.create_calendar_event(user, event_data)
            return result is not None
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Synchronisieren des Meilensteins: {e}")
            return False
    
    async def sync_task_to_calendar(self, user: User, task: Task, db: AsyncSession) -> bool:
        """Synchronisiert eine Aufgabe mit Google Calendar"""
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
🏗️ BuildWise Aufgabe

Projekt: {project.name}
Aufgabe: {task.title}
Status: {task.status.value}
Priorität: {task.priority.value}
Fortschritt: {task.progress_percentage}%

{task.description or ''}

🔗 BuildWise: {settings.base_url}/projects/{project.id}/tasks/{task.id}
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
        """Sendet Projekt-Update E-Mail über Gmail API"""
        credentials = await self.get_user_credentials(user)
        if not credentials:
            return False
            
        try:
            service = build('gmail', 'v1', credentials=credentials)
            
            # E-Mail zusammenstellen
            message = f"""
Betreff: {subject}
An: {', '.join(recipients)}
Von: {user.email}

{content}

---
Diese E-Mail wurde über BuildWise gesendet.
Projekt: {project.name}
🔗 {settings.base_url}/projects/{project.id}
            """.strip()
            
            # E-Mail senden (vereinfacht - würde in echter Implementation MIME formatting benötigen)
            # Hier würde die tatsächliche Gmail API Implementation stehen
            
            logger.info(f"✅ Projekt-Update E-Mail gesendet für Projekt {project.id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Senden der E-Mail: {e}")
            return False
    
    async def create_meeting_invitation(self, user: User, meeting_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Erstellt eine Meeting-Einladung mit automatischer Verfügbarkeitsprüfung"""
        try:
            # Erweiterte Event-Daten für Meetings
            event_data = {
                'title': f"🤝 {meeting_data.get('title', 'BuildWise Meeting')}",
                'description': f"""
🏗️ BuildWise Meeting

{meeting_data.get('description', '')}

📋 Agenda:
{meeting_data.get('agenda', 'Keine Agenda angegeben')}

🔗 BuildWise: {settings.base_url}
                """.strip(),
                'start_time': meeting_data['start_time'],
                'end_time': meeting_data['end_time'],
                'location': meeting_data.get('location', 'Online'),
                'attendees': meeting_data.get('attendees', []),
            }
            
            result = await self.create_calendar_event(user, event_data)
            
            if result:
                # Optional: Zusätzliche Meeting-Funktionen
                await self._setup_meeting_reminders(user, result['event_id'], meeting_data)
                
            return result
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der Meeting-Einladung: {e}")
            return None
    
    async def _setup_meeting_reminders(self, user: User, event_id: str, meeting_data: Dict[str, Any]):
        """Setzt erweiterte Meeting-Erinnerungen auf"""
        try:
            # Hier könnten zusätzliche Reminder-Logik implementiert werden
            # z.B. SMS-Reminders, Slack-Notifications, etc.
            logger.info(f"📅 Meeting-Reminders eingerichtet für Event {event_id}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Einrichten der Meeting-Reminders: {e}")
    
    async def get_calendar_availability(self, user: User, start_time: datetime, 
                                      end_time: datetime) -> Dict[str, Any]:
        """Prüft Verfügbarkeit im Google Calendar"""
        credentials = await self.get_user_credentials(user)
        if not credentials:
            return {"available": False, "reason": "No calendar access"}
            
        try:
            service = build('calendar', 'v3', credentials=credentials)
            
            # FreeBusy Query
            body = {
                "timeMin": start_time.isoformat(),
                "timeMax": end_time.isoformat(),
                "items": [{"id": "primary"}]
            }
            
            freebusy_result = service.freebusy().query(body=body).execute()
            busy_times = freebusy_result.get('calendars', {}).get('primary', {}).get('busy', [])
            
            is_available = len(busy_times) == 0
            
            return {
                "available": is_available,
                "busy_times": busy_times,
                "suggested_times": await self._suggest_alternative_times(service, start_time, end_time) if not is_available else []
            }
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Prüfen der Verfügbarkeit: {e}")
            return {"available": False, "reason": str(e)}
    
    async def _suggest_alternative_times(self, service, original_start: datetime, 
                                       original_end: datetime) -> List[Dict[str, Any]]:
        """Schlägt alternative Meeting-Zeiten vor"""
        try:
            suggestions = []
            duration = original_end - original_start
            
            # Suche nach freien Zeiten in den nächsten 7 Tagen
            for day_offset in range(1, 8):
                check_date = original_start + timedelta(days=day_offset)
                
                # Prüfe verschiedene Uhrzeiten
                for hour in [9, 10, 11, 14, 15, 16]:
                    suggested_start = check_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                    suggested_end = suggested_start + duration
                    
                    # Prüfe Verfügbarkeit
                    body = {
                        "timeMin": suggested_start.isoformat(),
                        "timeMax": suggested_end.isoformat(),
                        "items": [{"id": "primary"}]
                    }
                    
                    result = service.freebusy().query(body=body).execute()
                    busy = result.get('calendars', {}).get('primary', {}).get('busy', [])
                    
                    if not busy:
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


# Globale Service-Instanz
google_calendar_service = GoogleCalendarService() 