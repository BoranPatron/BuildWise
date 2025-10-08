"""
Calendar API Endpoints für BuildWise
Ermöglicht Google Calendar und Microsoft Outlook Integration
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query, BackgroundTasks
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models.user import User
from ..models.project import Project
from ..models.milestone import Milestone
from ..models.task import Task
from ..services.google_calendar_service import google_calendar_service
from ..services.microsoft_calendar_service import microsoft_calendar_service
from ..services.calendar_integration_service import calendar_integration_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic Models für API Requests
class CalendarEventRequest(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    attendees: List[str] = []
    timezone: str = "Europe/Zurich"

class MeetingRequest(BaseModel):
    title: str
    description: Optional[str] = None
    agenda: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = "Online"
    attendees: List[str] = []

class ProjectSyncRequest(BaseModel):
    project_id: int
    sync_milestones: bool = True
    sync_tasks: bool = True
    calendar_provider: str = "google"  # google, microsoft

class EmailNotificationRequest(BaseModel):
    project_id: int
    recipients: List[str]
    subject: str
    content: str
    provider: str = "google"  # google, microsoft

# Google Calendar Integration Endpoints

@router.get("/google/authorize")
async def google_calendar_authorize(
    current_user: User = Depends(get_current_user)
):
    """Startet Google Calendar OAuth2 Flow"""
    try:
        authorization_url = await google_calendar_service.get_authorization_url(current_user.id)
        return {"authorization_url": authorization_url}
        
    except Exception as e:
        logger.error(f"[ERROR] Google Calendar Authorization Fehler: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Starten der Google Calendar Authorization")

@router.get("/google/callback")
async def google_calendar_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Google Calendar OAuth2 Callback"""
    try:
        result = await google_calendar_service.handle_oauth_callback(code, state, db)
        
        if result["success"]:
            # Redirect to frontend with success message
            return RedirectResponse(url=f"/dashboard?calendar_connected=google&success=true")
        else:
            return RedirectResponse(url=f"/dashboard?calendar_connected=google&success=false")
            
    except Exception as e:
        logger.error(f"[ERROR] Google Calendar Callback Fehler: {e}")
        return RedirectResponse(url=f"/dashboard?calendar_connected=google&success=false&error={str(e)}")

@router.post("/google/create-event")
async def create_google_calendar_event(
    event_request: CalendarEventRequest,
    current_user: User = Depends(get_current_user)
):
    """Erstellt ein Event im Google Calendar"""
    try:
        event_data = {
            'title': event_request.title,
            'description': event_request.description,
            'start_time': event_request.start_time,
            'end_time': event_request.end_time,
            'location': event_request.location,
            'attendees': event_request.attendees,
            'timezone': event_request.timezone
        }
        
        result = await google_calendar_service.create_calendar_event(current_user, event_data)
        
        if result:
            return {
                "success": True,
                "message": "Google Calendar Event erfolgreich erstellt",
                "event_id": result['event_id'],
                "html_link": result.get('html_link')
            }
        else:
            raise HTTPException(status_code=400, detail="Fehler beim Erstellen des Google Calendar Events")
            
    except Exception as e:
        logger.error(f"[ERROR] Fehler beim Erstellen des Google Calendar Events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/google/sync-project")
async def sync_project_to_google_calendar(
    sync_request: ProjectSyncRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Synchronisiert ein Projekt mit Google Calendar"""
    try:
        # Lade Projekt
        project_result = await db.execute(
            select(Project).where(Project.id == sync_request.project_id)
        )
        project = project_result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
        
        synced_items = []
        
        # Synchronisiere Meilensteine
        if sync_request.sync_milestones:
            milestones_result = await db.execute(
                select(Milestone).where(Milestone.project_id == project.id)
            )
            milestones = milestones_result.scalars().all()
            
            for milestone in milestones:
                success = await google_calendar_service.sync_milestone_to_calendar(current_user, milestone, db)
                if success:
                    synced_items.append(f"Meilenstein: {milestone.title}")
        
        # Synchronisiere Aufgaben
        if sync_request.sync_tasks:
            tasks_result = await db.execute(
                select(Task).where(Task.project_id == project.id, Task.due_date.isnot(None))
            )
            tasks = tasks_result.scalars().all()
            
            for task in tasks:
                success = await google_calendar_service.sync_task_to_calendar(current_user, task, db)
                if success:
                    synced_items.append(f"Aufgabe: {task.title}")
        
        return {
            "success": True,
            "message": f"Projekt '{project.name}' erfolgreich mit Google Calendar synchronisiert",
            "synced_items": synced_items,
            "total_synced": len(synced_items)
        }
        
    except Exception as e:
        logger.error(f"[ERROR] Fehler bei Projekt-Synchronisation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Microsoft Calendar Integration Endpoints

@router.get("/microsoft/authorize")
async def microsoft_calendar_authorize(
    current_user: User = Depends(get_current_user)
):
    """Startet Microsoft Calendar OAuth2 Flow"""
    try:
        authorization_url = await microsoft_calendar_service.get_authorization_url(current_user.id)
        return {"authorization_url": authorization_url}
        
    except Exception as e:
        logger.error(f"[ERROR] Microsoft Calendar Authorization Fehler: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Starten der Microsoft Calendar Authorization")

@router.get("/microsoft/callback")
async def microsoft_calendar_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Microsoft Calendar OAuth2 Callback"""
    try:
        result = await microsoft_calendar_service.handle_oauth_callback(code, state, db)
        
        if result["success"]:
            return RedirectResponse(url=f"/dashboard?calendar_connected=microsoft&success=true")
        else:
            return RedirectResponse(url=f"/dashboard?calendar_connected=microsoft&success=false")
            
    except Exception as e:
        logger.error(f"[ERROR] Microsoft Calendar Callback Fehler: {e}")
        return RedirectResponse(url=f"/dashboard?calendar_connected=microsoft&success=false&error={str(e)}")

@router.post("/microsoft/create-event")
async def create_microsoft_calendar_event(
    event_request: CalendarEventRequest,
    current_user: User = Depends(get_current_user)
):
    """Erstellt ein Event im Microsoft Calendar"""
    try:
        event_data = {
            'title': event_request.title,
            'description': event_request.description,
            'start_time': event_request.start_time,
            'end_time': event_request.end_time,
            'location': event_request.location,
            'attendees': event_request.attendees,
            'timezone': event_request.timezone
        }
        
        result = await microsoft_calendar_service.create_calendar_event(current_user, event_data)
        
        if result:
            return {
                "success": True,
                "message": "Microsoft Calendar Event erfolgreich erstellt",
                "event_id": result['event_id'],
                "web_link": result.get('web_link')
            }
        else:
            raise HTTPException(status_code=400, detail="Fehler beim Erstellen des Microsoft Calendar Events")
            
    except Exception as e:
        logger.error(f"[ERROR] Fehler beim Erstellen des Microsoft Calendar Events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Meeting Management Endpoints

@router.post("/create-meeting")
async def create_meeting_invitation(
    meeting_request: MeetingRequest,
    provider: str = Query("google", description="Calendar provider: google or microsoft"),
    current_user: User = Depends(get_current_user)
):
    """Erstellt eine Meeting-Einladung"""
    try:
        meeting_data = {
            'title': meeting_request.title,
            'description': meeting_request.description,
            'agenda': meeting_request.agenda,
            'start_time': meeting_request.start_time,
            'end_time': meeting_request.end_time,
            'location': meeting_request.location,
            'attendees': meeting_request.attendees
        }
        
        if provider == "google":
            result = await google_calendar_service.create_meeting_invitation(current_user, meeting_data)
        elif provider == "microsoft":
            result = await microsoft_calendar_service.create_meeting_invitation(current_user, meeting_data)
        else:
            raise HTTPException(status_code=400, detail="Unsupported calendar provider")
        
        if result:
            return {
                "success": True,
                "message": f"Meeting-Einladung über {provider} erstellt",
                "event_id": result['event_id'],
                "meeting_link": result.get('html_link') or result.get('web_link')
            }
        else:
            raise HTTPException(status_code=400, detail="Fehler beim Erstellen der Meeting-Einladung")
            
    except Exception as e:
        logger.error(f"[ERROR] Fehler beim Erstellen der Meeting-Einladung: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/availability")
async def check_calendar_availability(
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    provider: str = Query("google", description="Calendar provider: google or microsoft"),
    current_user: User = Depends(get_current_user)
):
    """Prüft Verfügbarkeit im Kalender"""
    try:
        if provider == "google":
            availability = await google_calendar_service.get_calendar_availability(
                current_user, start_time, end_time
            )
        elif provider == "microsoft":
            availability = await microsoft_calendar_service.get_calendar_availability(
                current_user, start_time, end_time
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported calendar provider")
        
        return {
            "available": availability.get("available", False),
            "busy_times": availability.get("busy_times", []),
            "suggested_times": availability.get("suggested_times", []),
            "provider": provider
        }
        
    except Exception as e:
        logger.error(f"[ERROR] Fehler bei Verfügbarkeitsprüfung: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ICS Download Endpoints

@router.get("/download/project/{project_id}")
async def download_project_calendar(
    project_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lädt Projekt-Kalender als ICS-Datei herunter"""
    try:
        # Lade Projekt
        project_result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
        
        # Lade Meilensteine und Aufgaben
        milestones_result = await db.execute(
            select(Milestone).where(Milestone.project_id == project.id)
        )
        milestones = milestones_result.scalars().all()
        
        tasks_result = await db.execute(
            select(Task).where(Task.project_id == project.id, Task.due_date.isnot(None))
        )
        tasks = tasks_result.scalars().all()
        
        # Generiere ICS-Datei
        ics_file_path = await calendar_integration_service.generate_project_ics(
            project, milestones, tasks, current_user
        )
        
        # Cleanup nach Download
        background_tasks.add_task(calendar_integration_service.cleanup_temp_file, ics_file_path)
        
        return FileResponse(
            path=ics_file_path,
            media_type='text/calendar',
            filename=f'BuildWise-{project.name.replace(" ", "_")}.ics'
        )
        
    except Exception as e:
        logger.error(f"[ERROR] Fehler beim Download der Projekt-ICS: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/milestone/{milestone_id}")
async def download_milestone_calendar(
    milestone_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lädt Meilenstein als ICS-Datei herunter"""
    try:
        # Lade Meilenstein und Projekt
        milestone_result = await db.execute(
            select(Milestone).where(Milestone.id == milestone_id)
        )
        milestone = milestone_result.scalar_one_or_none()
        
        if not milestone:
            raise HTTPException(status_code=404, detail="Meilenstein nicht gefunden")
        
        project_result = await db.execute(
            select(Project).where(Project.id == milestone.project_id)
        )
        project = project_result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
        
        # Generiere ICS-Datei
        ics_file_path = await calendar_integration_service.generate_milestone_ics(
            milestone, project, current_user
        )
        
        # Cleanup nach Download
        background_tasks.add_task(calendar_integration_service.cleanup_temp_file, ics_file_path)
        
        return FileResponse(
            path=ics_file_path,
            media_type='text/calendar',
            filename=f'BuildWise-Meilenstein-{milestone.title.replace(" ", "_")}.ics'
        )
        
    except Exception as e:
        logger.error(f"[ERROR] Fehler beim Download der Meilenstein-ICS: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/add-to-calendar")
async def get_add_to_calendar_links(
    title: str = Query(...),
    description: str = Query(""),
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    location: str = Query("")
):
    """Generiert Add-to-Calendar Links für verschiedene Anbieter"""
    try:
        event_data = {
            'title': title,
            'description': description,
            'start_time': start_time,
            'end_time': end_time,
            'location': location
        }
        
        links = await calendar_integration_service.generate_add_to_calendar_links(event_data)
        
        return {
            "success": True,
            "links": links
        }
        
    except Exception as e:
        logger.error(f"[ERROR] Fehler beim Generieren der Kalender-Links: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Email Integration Endpoints

@router.post("/send-project-update")
async def send_project_update_email(
    email_request: EmailNotificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Sendet Projekt-Update E-Mail"""
    try:
        # Lade Projekt
        project_result = await db.execute(
            select(Project).where(Project.id == email_request.project_id)
        )
        project = project_result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
        
        # Sende E-Mail
        if email_request.provider == "google":
            success = await google_calendar_service.send_project_update_email(
                current_user, project, email_request.recipients, 
                email_request.subject, email_request.content
            )
        elif email_request.provider == "microsoft":
            success = await microsoft_calendar_service.send_project_update_email(
                current_user, project, email_request.recipients,
                email_request.subject, email_request.content
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported email provider")
        
        if success:
            return {
                "success": True,
                "message": f"Projekt-Update E-Mail über {email_request.provider} gesendet",
                "recipients_count": len(email_request.recipients)
            }
        else:
            raise HTTPException(status_code=400, detail="Fehler beim Senden der E-Mail")
            
    except Exception as e:
        logger.error(f"[ERROR] Fehler beim Senden der Projekt-Update E-Mail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Calendar Status Endpoints

@router.get("/status")
async def get_calendar_integration_status(
    current_user: User = Depends(get_current_user)
):
    """Zeigt Status der Kalender-Integrationen"""
    return {
        "user_id": current_user.id,
        "google_calendar": {
            "enabled": current_user.google_calendar_enabled or False,
            "connected": bool(current_user.google_calendar_token),
            "token_expires": current_user.google_calendar_token_expiry.isoformat() if current_user.google_calendar_token_expiry else None
        },
        "microsoft_calendar": {
            "enabled": current_user.microsoft_calendar_enabled or False,
            "connected": bool(current_user.microsoft_calendar_token),
            "token_expires": current_user.microsoft_calendar_token_expiry.isoformat() if current_user.microsoft_calendar_token_expiry else None
        }
    }

@router.delete("/disconnect/{provider}")
async def disconnect_calendar_provider(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Trennt Verbindung zu einem Kalender-Anbieter"""
    try:
        if provider == "google":
            await db.execute(
                update(User)
                .where(User.id == current_user.id)
                .values(
                    google_calendar_enabled=False,
                    google_calendar_token=None,
                    google_calendar_refresh_token=None,
                    google_calendar_token_expiry=None
                )
            )
        elif provider == "microsoft":
            await db.execute(
                update(User)
                .where(User.id == current_user.id)
                .values(
                    microsoft_calendar_enabled=False,
                    microsoft_calendar_token=None,
                    microsoft_calendar_refresh_token=None,
                    microsoft_calendar_token_expiry=None
                )
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported calendar provider")
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"{provider.title()} Calendar erfolgreich getrennt"
        }
        
    except Exception as e:
        logger.error(f"[ERROR] Fehler beim Trennen der Kalender-Verbindung: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 