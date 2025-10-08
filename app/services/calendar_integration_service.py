"""
Calendar Integration Service für BuildWise
Generiert ICS-Dateien und verwaltet Kalender-Downloads
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from icalendar import Calendar, Event, vCalAddress, vText
import tempfile
import os
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.user import User
from ..models.milestone import Milestone
from ..models.project import Project
from ..models.task import Task
from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class CalendarIntegrationService:
    """Service für Kalender-Integration und ICS-Generation"""
    
    def __init__(self):
        pass
    
    async def generate_project_ics(self, project: Project, milestones: List[Milestone], 
                                  tasks: List[Task], user: User) -> str:
        """Generiert ICS-Datei für ein Projekt mit allen Meilensteinen und Aufgaben"""
        try:
            cal = Calendar()
            cal.add('prodid', '-//BuildWise//BuildWise Calendar//DE')
            cal.add('version', '2.0')
            cal.add('calscale', 'GREGORIAN')
            cal.add('method', 'PUBLISH')
            cal.add('x-wr-calname', f'BuildWise - {project.name}')
            cal.add('x-wr-caldesc', f'Meilensteine und Aufgaben für Projekt: {project.name}')
            
            # Meilensteine hinzufügen
            for milestone in milestones:
                event = Event()
                event.add('uid', f'milestone-{milestone.id}@buildwise.de')
                event.add('dtstart', milestone.planned_date)
                event.add('dtend', milestone.planned_date)
                event.add('summary', f'[INFO] {milestone.title}')
                event.add('description', f"""
BuildWise Meilenstein

Projekt: {project.name}
Meilenstein: {milestone.title}
Status: {milestone.status.value}
Priorität: {milestone.priority.value}

{milestone.description or ''}

🔗 BuildWise: {settings.base_url}/projects/{project.id}
                """.strip())
                
                if project.address:
                    event.add('location', project.address)
                
                # Organizer
                organizer = vCalAddress(f'mailto:{user.email}')
                organizer.params['cn'] = vText(f'{user.first_name} {user.last_name}')
                event.add('organizer', organizer)
                
                # Alarm/Reminder
                alarm = event.add('valarm')
                alarm.add('action', 'DISPLAY')
                alarm.add('description', f'Erinnerung: {milestone.title}')
                alarm.add('trigger', timedelta(hours=-24))  # 1 Tag vorher
                
                event.add('created', datetime.now())
                event.add('last-modified', milestone.updated_at or datetime.now())
                event.add('categories', ['BuildWise', 'Meilenstein', project.name])
                
                cal.add_component(event)
            
            # Aufgaben hinzufügen
            for task in tasks:
                if not task.due_date:
                    continue
                    
                event = Event()
                event.add('uid', f'task-{task.id}@buildwise.de')
                event.add('dtstart', task.due_date)
                event.add('dtend', task.due_date)
                event.add('summary', f'[SUCCESS] {task.title}')
                event.add('description', f"""
BuildWise Aufgabe

Projekt: {project.name}
Aufgabe: {task.title}
Status: {task.status.value}
Priorität: {task.priority.value}
Fortschritt: {task.progress_percentage}%

{task.description or ''}

🔗 BuildWise: {settings.base_url}/projects/{project.id}/tasks/{task.id}
                """.strip())
                
                if project.address:
                    event.add('location', project.address)
                
                # Organizer
                organizer = vCalAddress(f'mailto:{user.email}')
                organizer.params['cn'] = vText(f'{user.first_name} {user.last_name}')
                event.add('organizer', organizer)
                
                # Assigned User als Attendee
                if task.assigned_to and task.assigned_user:
                    attendee = vCalAddress(f'mailto:{task.assigned_user.email}')
                    attendee.params['cn'] = vText(f'{task.assigned_user.first_name} {task.assigned_user.last_name}')
                    attendee.params['role'] = vText('REQ-PARTICIPANT')
                    event.add('attendee', attendee)
                
                # Alarm/Reminder
                alarm = event.add('valarm')
                alarm.add('action', 'DISPLAY')
                alarm.add('description', f'Erinnerung: {task.title}')
                alarm.add('trigger', timedelta(hours=-2))  # 2 Stunden vorher
                
                event.add('created', datetime.now())
                event.add('last-modified', task.updated_at or datetime.now())
                event.add('categories', ['BuildWise', 'Aufgabe', project.name])
                
                cal.add_component(event)
            
            # ICS-Datei generieren
            ics_content = cal.to_ical().decode('utf-8')
            
            # Temporäre Datei erstellen
            temp_file = tempfile.NamedTemporaryFile(mode='w+', suffix='.ics', delete=False)
            temp_file.write(ics_content)
            temp_file.close()
            
            logger.info(f"[SUCCESS] ICS-Datei generiert für Projekt {project.id}: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"[ERROR] Fehler beim Generieren der ICS-Datei: {e}")
            raise
    
    async def generate_milestone_ics(self, milestone: Milestone, project: Project, user: User) -> str:
        """Generiert ICS-Datei für einen einzelnen Meilenstein"""
        try:
            cal = Calendar()
            cal.add('prodid', '-//BuildWise//BuildWise Calendar//DE')
            cal.add('version', '2.0')
            cal.add('calscale', 'GREGORIAN')
            cal.add('method', 'PUBLISH')
            
            event = Event()
            event.add('uid', f'milestone-{milestone.id}@buildwise.de')
            event.add('dtstart', milestone.planned_date)
            event.add('dtend', milestone.planned_date)
            event.add('summary', f'[INFO] {milestone.title} - {project.name}')
            event.add('description', f"""
BuildWise Meilenstein

Projekt: {project.name}
Meilenstein: {milestone.title}
Status: {milestone.status.value}
Priorität: {milestone.priority.value}
Budget: {milestone.budget or 'Nicht definiert'}

{milestone.description or ''}

🔗 BuildWise: {settings.base_url}/projects/{project.id}
            """.strip())
            
            if project.address:
                event.add('location', project.address)
            
            # Organizer
            organizer = vCalAddress(f'mailto:{user.email}')
            organizer.params['cn'] = vText(f'{user.first_name} {user.last_name}')
            event.add('organizer', organizer)
            
            # Alarm/Reminder
            alarm = event.add('valarm')
            alarm.add('action', 'DISPLAY')
            alarm.add('description', f'Erinnerung: {milestone.title}')
            alarm.add('trigger', timedelta(hours=-24))  # 1 Tag vorher
            
            event.add('created', datetime.now())
            event.add('last-modified', milestone.updated_at or datetime.now())
            event.add('categories', ['BuildWise', 'Meilenstein', project.name])
            
            cal.add_component(event)
            
            # ICS-Datei generieren
            ics_content = cal.to_ical().decode('utf-8')
            
            # Temporäre Datei erstellen
            temp_file = tempfile.NamedTemporaryFile(mode='w+', suffix='.ics', delete=False)
            temp_file.write(ics_content)
            temp_file.close()
            
            logger.info(f"[SUCCESS] ICS-Datei generiert für Meilenstein {milestone.id}: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"[ERROR] Fehler beim Generieren der Meilenstein-ICS-Datei: {e}")
            raise
    
    async def generate_meeting_ics(self, meeting_data: Dict[str, Any], user: User) -> str:
        """Generiert ICS-Datei für ein Meeting"""
        try:
            cal = Calendar()
            cal.add('prodid', '-//BuildWise//BuildWise Calendar//DE')
            cal.add('version', '2.0')
            cal.add('calscale', 'GREGORIAN')
            cal.add('method', 'REQUEST')
            
            event = Event()
            event.add('uid', f'meeting-{datetime.now().timestamp()}@buildwise.de')
            event.add('dtstart', meeting_data['start_time'])
            event.add('dtend', meeting_data['end_time'])
            event.add('summary', f"🤝 {meeting_data.get('title', 'BuildWise Meeting')}")
            event.add('description', f"""
BuildWise Meeting

{meeting_data.get('description', '')}

[INFO] Agenda:
{meeting_data.get('agenda', 'Keine Agenda angegeben')}

🔗 BuildWise: {settings.base_url}
            """.strip())
            
            if meeting_data.get('location'):
                event.add('location', meeting_data['location'])
            
            # Organizer
            organizer = vCalAddress(f'mailto:{user.email}')
            organizer.params['cn'] = vText(f'{user.first_name} {user.last_name}')
            organizer.params['role'] = vText('CHAIR')
            event.add('organizer', organizer)
            
            # Attendees
            for attendee_email in meeting_data.get('attendees', []):
                attendee = vCalAddress(f'mailto:{attendee_email}')
                attendee.params['cn'] = vText(attendee_email.split('@')[0])
                attendee.params['role'] = vText('REQ-PARTICIPANT')
                attendee.params['partstat'] = vText('NEEDS-ACTION')
                attendee.params['rsvp'] = vText('TRUE')
                event.add('attendee', attendee)
            
            # Meeting-spezifische Eigenschaften
            event.add('status', 'CONFIRMED')
            event.add('transp', 'OPAQUE')
            event.add('sequence', 0)
            
            # Alarm/Reminder
            alarm = event.add('valarm')
            alarm.add('action', 'DISPLAY')
            alarm.add('description', f"Erinnerung: {meeting_data.get('title', 'Meeting')}")
            alarm.add('trigger', timedelta(minutes=-15))  # 15 Min vorher
            
            event.add('created', datetime.now())
            event.add('dtstamp', datetime.now())
            event.add('last-modified', datetime.now())
            event.add('categories', ['BuildWise', 'Meeting'])
            
            cal.add_component(event)
            
            # ICS-Datei generieren
            ics_content = cal.to_ical().decode('utf-8')
            
            # Temporäre Datei erstellen
            temp_file = tempfile.NamedTemporaryFile(mode='w+', suffix='.ics', delete=False)
            temp_file.write(ics_content)
            temp_file.close()
            
            logger.info(f"[SUCCESS] Meeting-ICS-Datei generiert: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"[ERROR] Fehler beim Generieren der Meeting-ICS-Datei: {e}")
            raise
    
    def cleanup_temp_file(self, file_path: str):
        """Räumt temporäre ICS-Dateien auf"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.info(f"🗑️ Temporäre Datei gelöscht: {file_path}")
        except Exception as e:
            logger.error(f"[ERROR] Fehler beim Löschen der temporären Datei: {e}")
    
    async def generate_add_to_calendar_links(self, event_data: Dict[str, Any]) -> Dict[str, str]:
        """Generiert Add-to-Calendar Links für verschiedene Anbieter"""
        try:
            title = event_data.get('title', 'BuildWise Event')
            description = event_data.get('description', '').replace('\n', ' ')
            location = event_data.get('location', '')
            start_time = event_data['start_time']
            end_time = event_data['end_time']
            
            # Google Calendar Link
            google_params = {
                'action': 'TEMPLATE',
                'text': title,
                'dates': f"{start_time.strftime('%Y%m%dT%H%M%S')}/{end_time.strftime('%Y%m%dT%H%M%S')}",
                'details': description,
                'location': location
            }
            google_url = f"https://calendar.google.com/calendar/render?{'&'.join([f'{k}={v}' for k, v in google_params.items()])}"
            
            # Outlook Web Link
            outlook_params = {
                'subject': title,
                'startdt': start_time.isoformat(),
                'enddt': end_time.isoformat(),
                'body': description,
                'location': location
            }
            outlook_url = f"https://outlook.live.com/calendar/0/deeplink/compose?{'&'.join([f'{k}={v}' for k, v in outlook_params.items()])}"
            
            # Yahoo Calendar Link
            yahoo_params = {
                'v': '60',
                'title': title,
                'st': start_time.strftime('%Y%m%dT%H%M%S'),
                'et': end_time.strftime('%Y%m%dT%H%M%S'),
                'desc': description,
                'in_loc': location
            }
            yahoo_url = f"https://calendar.yahoo.com/?{'&'.join([f'{k}={v}' for k, v in yahoo_params.items()])}"
            
            return {
                'google': google_url,
                'outlook': outlook_url,
                'yahoo': yahoo_url,
                'ics_download': f"{settings.base_url}/api/v1/calendar/download/event/{event_data.get('id', 'temp')}"
            }
            
        except Exception as e:
            logger.error(f"[ERROR] Fehler beim Generieren der Kalender-Links: {e}")
            return {}
    
    async def create_recurring_events(self, event_data: Dict[str, Any], 
                                     recurrence_rule: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Erstellt wiederkehrende Events basierend auf Recurrence-Regeln"""
        try:
            events = []
            start_date = event_data['start_time']
            end_date = event_data['end_time']
            duration = end_date - start_date
            
            frequency = recurrence_rule.get('frequency', 'weekly')  # daily, weekly, monthly
            interval = recurrence_rule.get('interval', 1)
            count = recurrence_rule.get('count', 10)  # Anzahl Wiederholungen
            until_date = recurrence_rule.get('until_date')
            
            current_start = start_date
            
            for i in range(count):
                if until_date and current_start > until_date:
                    break
                
                event_copy = event_data.copy()
                event_copy['start_time'] = current_start
                event_copy['end_time'] = current_start + duration
                event_copy['title'] = f"{event_data['title']} ({i+1}/{count})"
                event_copy['recurrence_id'] = i
                
                events.append(event_copy)
                
                # Nächstes Datum berechnen
                if frequency == 'daily':
                    current_start += timedelta(days=interval)
                elif frequency == 'weekly':
                    current_start += timedelta(weeks=interval)
                elif frequency == 'monthly':
                    # Vereinfachte monatliche Wiederholung
                    if current_start.month == 12:
                        current_start = current_start.replace(year=current_start.year + 1, month=1)
                    else:
                        current_start = current_start.replace(month=current_start.month + interval)
                
            logger.info(f"[SUCCESS] {len(events)} wiederkehrende Events erstellt")
            return events
            
        except Exception as e:
            logger.error(f"[ERROR] Fehler beim Erstellen wiederkehrender Events: {e}")
            return []


# Globale Service-Instanz
calendar_integration_service = CalendarIntegrationService() 