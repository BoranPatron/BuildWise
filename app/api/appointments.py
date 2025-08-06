from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Union
from datetime import datetime
import json

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models import User, Appointment, AppointmentStatus
from ..schemas.appointment import (
    AppointmentCreate, AppointmentUpdate, AppointmentResponse,
    InspectionDecisionRequest, AppointmentResponseRequest,
    CalendarEventData, NotificationRequest
)
from ..services.appointment_service import AppointmentService

router = APIRouter(prefix="/appointments", tags=["appointments"])

# WICHTIG: Spezifische Routes müssen VOR parametrisierten Routes definiert werden!
# Sonst fängt "/{appointment_id}" alle anderen Routes ab!


@router.delete("/debug/delete-all-appointments")
async def delete_all_appointments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Debug-Endpoint zum Löschen aller Termine"""
    try:
        # Prüfe ob User ein Admin oder Bauträger ist
        from ..models.user import UserRole
        if not (current_user.user_role == UserRole.ADMIN or current_user.user_role == UserRole.BAUTRAEGER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Admins und Bauträger können alle Termine löschen"
            )
        
        # Lösche alle Termine
        from sqlalchemy import text
        
        # Lösche zuerst die Termin-Antworten
        await db.execute(text("DELETE FROM appointment_responses"))
        
        # Dann lösche die Termine
        await db.execute(text("DELETE FROM appointments"))
        
        await db.commit()
        
        return {"message": "Alle Termine und Termin-Antworten wurden gelöscht"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Löschen der Termine: {str(e)}"
        )


@router.get("/test-simple")
async def test_simple():
    """Einfacher Test ohne Dependencies"""
    print("🔧 TEST: test_simple aufgerufen")
    return {"message": "test_simple funktioniert"}


@router.get("/test-with-user")
async def test_with_user(current_user: User = Depends(get_current_user)):
    """Test mit User Dependency"""
    print(f"🔧 TEST: test_with_user aufgerufen, user_id={current_user.id}")
    return {"message": "test_with_user funktioniert", "user_id": current_user.id}


@router.get("/test-with-db")
async def test_with_db(db: AsyncSession = Depends(get_db)):
    """Test mit DB Dependency"""
    print("🔧 TEST: test_with_db aufgerufen")
    return {"message": "test_with_db funktioniert"}


@router.get("/test-with-query")
async def test_with_query(project_id: Optional[int] = Query(None)):
    """Test mit Query Parameter"""
    print(f"🔧 TEST: test_with_query aufgerufen, project_id={project_id}")
    return {"message": "test_with_query funktioniert", "project_id": project_id}


@router.get("/test-no-deps")
async def test_no_deps():
    """Test ohne JEGLICHE Dependencies"""
    print("🎯 TEST-NO-DEPS: Endpoint wurde erreicht!")
    return {"message": "test-no-deps funktioniert", "timestamp": str(datetime.utcnow())}


@router.get("/my-appointments-dienstleister")
async def get_my_appointments_dienstleister(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """SPEZIELLER Endpoint für Dienstleister - filtert nach invited_service_providers"""
    try:
        print(f"🔧 get_my_appointments_dienstleister called for user_id={current_user.id}")
        
        from sqlalchemy import text
        import json
        
        # Lade alle Termine
        query = text("""
            SELECT 
                id, project_id, trade_id, milestone_id, created_by, 
                title, description, appointment_type, status,
                scheduled_date, duration_minutes, location, location_details,
                notes, invited_service_providers, responses,
                inspection_completed, inspection_notes,
                selected_service_provider_id, requires_renegotiation,
                renegotiation_details, notification_sent,
                follow_up_notification_date, follow_up_sent,
                created_at, updated_at, completed_at
            FROM appointments 
            ORDER BY scheduled_date DESC
        """)
        
        result = await db.execute(query)
        all_appointments = result.fetchall()
        
        print(f"🔍 Found {len(all_appointments)} total appointments")
        
        # Filtere nur Termine, zu denen der Dienstleister eingeladen ist
        filtered_appointments = []
        for apt in all_appointments:
            if apt.invited_service_providers:
                try:
                    # Parse JSON
                    if isinstance(apt.invited_service_providers, str):
                        invited_providers = json.loads(apt.invited_service_providers)
                    else:
                        invited_providers = apt.invited_service_providers
                    
                    # Prüfe ob User eingeladen ist
                    if isinstance(invited_providers, list):
                        invited_ids = [provider.get('id') for provider in invited_providers if isinstance(provider, dict)]
                        if current_user.id in invited_ids:
                            filtered_appointments.append(apt)
                            print(f"✅ User {current_user.id} ist zu Termin {apt.id} eingeladen")
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"⚠️ JSON-Fehler bei Termin {apt.id}: {e}")
                    continue
        
        print(f"🔧 Dienstleister {current_user.id} hat Zugriff auf {len(filtered_appointments)} Termine")
        
        # Konvertiere zu einfachem Dictionary
        simple_appointments = []
        
        # Sichere Datum-Konvertierung
        def safe_isoformat(value):
            if value is None:
                return None
            if isinstance(value, str):
                return value
            if hasattr(value, 'isoformat'):
                return value.isoformat()
            return str(value)
        
        for apt in filtered_appointments:
            simple_appointment = {
                "id": apt.id,
                "project_id": apt.project_id,
                "trade_id": apt.trade_id,
                "milestone_id": apt.milestone_id,
                "created_by": apt.created_by,
                "title": apt.title,
                "description": apt.description,
                "appointment_type": apt.appointment_type,
                "status": apt.status,
                "scheduled_date": safe_isoformat(apt.scheduled_date),
                "duration_minutes": apt.duration_minutes,
                "location": apt.location,
                "location_details": apt.location_details,
                "notes": apt.notes,
                "invited_service_providers": apt.invited_service_providers,
                "responses": apt.responses,
                "inspection_completed": bool(apt.inspection_completed),
                "selected_service_provider_id": apt.selected_service_provider_id,
                "inspection_notes": apt.inspection_notes,
                "requires_renegotiation": bool(apt.requires_renegotiation),
                "renegotiation_details": apt.renegotiation_details,
                "notification_sent": bool(apt.notification_sent),
                "follow_up_notification_date": safe_isoformat(apt.follow_up_notification_date),
                "follow_up_sent": bool(apt.follow_up_sent),
                "created_at": safe_isoformat(apt.created_at),
                "updated_at": safe_isoformat(apt.updated_at),
                "completed_at": safe_isoformat(apt.completed_at)
            }
            simple_appointments.append(simple_appointment)
        
        print(f"✅ Successfully converted {len(simple_appointments)} appointments for Dienstleister")
        return {"appointments": simple_appointments, "count": len(simple_appointments)}
        
    except Exception as e:
        print(f"❌ Error in get_my_appointments_dienstleister: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return {"appointments": [], "count": 0, "error": str(e)}


@router.get("/my-appointments")
async def get_my_appointments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Hole alle Termine des aktuellen Benutzers basierend auf seiner Rolle
    
    - Bauträger: Nur eigene erstellte Termine
    - Dienstleister: Nur Termine zu denen sie eingeladen wurden  
    - Admin: Alle Termine
    """
    try:
        print(f"🔍 get_my_appointments called for user_id={current_user.id}, user_role={current_user.user_role}")
        print(f"🔍 DEBUG: current_user object: {current_user}")
        print(f"🔍 DEBUG: current_user.user_role type: {type(current_user.user_role)}")
        print(f"🔍 DEBUG: current_user.user_role value: '{current_user.user_role}'")
        
        print(f"🔍 Rufe AppointmentService.get_appointments_for_user auf...")
        appointments = await AppointmentService.get_appointments_for_user(
            db=db,
            user=current_user,
            project_id=None  # Kein Projekt-Filter für jetzt
        )
        print(f"✅ AppointmentService.get_appointments_for_user abgeschlossen")
        
        print(f"✅ Found {len(appointments)} appointments for user {current_user.id}")
        
        # Konvertiere zu AppointmentResponse-Objekten
        response_appointments = []
        for appointment in appointments:
            try:
                # Parse invited_service_providers JSON
                invited_providers = None
                if appointment.invited_service_providers:
                    if isinstance(appointment.invited_service_providers, str):
                        invited_providers = json.loads(appointment.invited_service_providers)
                    else:
                        invited_providers = appointment.invited_service_providers
                
                # Parse responses JSON
                responses = None
                if appointment.responses:
                    if isinstance(appointment.responses, str):
                        responses = json.loads(appointment.responses)
                    else:
                        responses = appointment.responses
                
                response_appointment = AppointmentResponse(
                    id=appointment.id,
                    project_id=appointment.project_id,
                    milestone_id=appointment.milestone_id,
                    created_by=appointment.created_by,
                    title=appointment.title,
                    description=appointment.description,
                    appointment_type=appointment.appointment_type,
                    status=appointment.status,
                    scheduled_date=appointment.scheduled_date,
                    duration_minutes=appointment.duration_minutes,
                    location=appointment.location,
                    location_details=appointment.location_details,
                    invited_service_providers=invited_providers,
                    responses=responses,
                    inspection_completed=appointment.inspection_completed,
                    selected_service_provider_id=appointment.selected_service_provider_id,
                    inspection_notes=appointment.inspection_notes,
                    requires_renegotiation=appointment.requires_renegotiation,
                    renegotiation_details=appointment.renegotiation_details,
                    notification_sent=appointment.notification_sent,
                    follow_up_notification_date=appointment.follow_up_notification_date,
                    follow_up_sent=appointment.follow_up_sent,
                    created_at=appointment.created_at,
                    updated_at=appointment.updated_at,
                    completed_at=appointment.completed_at
                )
                response_appointments.append(response_appointment)
                
            except Exception as e:
                print(f"⚠️ Fehler beim Konvertieren von Appointment {appointment.id}: {e}")
                continue
        
        print(f"✅ Successfully converted {len(response_appointments)} appointments")
        return response_appointments
        
    except Exception as e:
        print(f"❌ Error in get_my_appointments: {e}")
        print(f"🔄 Fallback: Returning empty list for user {current_user.id}")
        # Fallback: Leere Liste zurückgeben statt Fehler
        return []


@router.get("/my-appointments-simple")
async def get_my_appointments_simple(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    EINFACHER Endpoint für Appointments - umgeht Schema-Validierung
    Arbeitet direkt mit der echten Datenbankstruktur
    """
    try:
        print(f"🔍 get_my_appointments_simple called for user_id={current_user.id}")
        
        # Erweiterte Abfrage mit AppointmentResponse Tabelle
        from sqlalchemy import text, select
        from app.models.appointment_response import AppointmentResponse
        
        # Für Dienstleister: Alle Termine laden und dann in Python filtern
        # (da JSON-Filterung in SQLite komplex ist)
        if current_user.user_role.value == "DIENSTLEISTER":
            print(f"🔧 Dienstleister: Lade alle Termine für JSON-Filterung")
            query = text("""
                SELECT 
                    id, project_id, trade_id, milestone_id, created_by, 
                    title, description, appointment_type, status,
                    scheduled_date, duration_minutes, location, location_details,
                    notes, invited_service_providers, responses,
                    inspection_completed, inspection_notes,
                    selected_service_provider_id, requires_renegotiation,
                    renegotiation_details, notification_sent,
                    follow_up_notification_date, follow_up_sent,
                    created_at, updated_at, completed_at
                FROM appointments 
                ORDER BY scheduled_date DESC
            """)
        else:
            # Für Bauträger: Nur eigene Termine
            print(f"🏗️ Bauträger: Lade nur eigene Termine")
            query = text("""
                SELECT 
                    id, project_id, trade_id, milestone_id, created_by, 
                    title, description, appointment_type, status,
                    scheduled_date, duration_minutes, location, location_details,
                    notes, invited_service_providers, responses,
                    inspection_completed, inspection_notes,
                    selected_service_provider_id, requires_renegotiation,
                    renegotiation_details, notification_sent,
                    follow_up_notification_date, follow_up_sent,
                    created_at, updated_at, completed_at
                FROM appointments 
                WHERE created_by = :user_id
                ORDER BY scheduled_date DESC
            """)
        
        result = await db.execute(query, {"user_id": current_user.id})
        appointments = result.fetchall()
        
        print(f"✅ Found {len(appointments)} appointments via SQL query")
        
        # Konvertiere zu einfachem Dictionary
        simple_appointments = []
        
        # Sichere Datum-Konvertierung
        def safe_isoformat(value):
            if value is None:
                return None
            if isinstance(value, str):
                return value
            if hasattr(value, 'isoformat'):
                return value.isoformat()
            return str(value)
        
        for apt in appointments:
            simple_appointment = {
                "id": apt.id,
                "project_id": apt.project_id,
                "trade_id": apt.trade_id,
                "milestone_id": apt.milestone_id,
                "created_by": apt.created_by,
                "title": apt.title,
                "description": apt.description,
                "appointment_type": apt.appointment_type,
                "status": apt.status,
                "scheduled_date": safe_isoformat(apt.scheduled_date),
                "duration_minutes": apt.duration_minutes,
                "location": apt.location,
                "location_details": apt.location_details,
                "notes": apt.notes,
                "invited_service_providers": apt.invited_service_providers,
                "responses": apt.responses,
                "inspection_completed": bool(apt.inspection_completed),
                "selected_service_provider_id": apt.selected_service_provider_id,
                "inspection_notes": apt.inspection_notes,
                "requires_renegotiation": bool(apt.requires_renegotiation),
                "renegotiation_details": apt.renegotiation_details,
                "notification_sent": bool(apt.notification_sent),
                "follow_up_notification_date": safe_isoformat(apt.follow_up_notification_date),
                "follow_up_sent": bool(apt.follow_up_sent),
                "created_at": safe_isoformat(apt.created_at),
                "updated_at": safe_isoformat(apt.updated_at),
                "completed_at": safe_isoformat(apt.completed_at)
            }
            simple_appointments.append(simple_appointment)
        
        # Lade alle Responses für diese Appointments aus der neuen Tabelle
        appointment_ids = [apt["id"] for apt in simple_appointments]
        if appointment_ids:
            responses_stmt = select(AppointmentResponse).where(AppointmentResponse.appointment_id.in_(appointment_ids))
            responses_result = await db.execute(responses_stmt)
            all_responses = responses_result.scalars().all()
            
            # Gruppiere Responses nach appointment_id
            responses_by_appointment = {}
            for response in all_responses:
                if response.appointment_id not in responses_by_appointment:
                    responses_by_appointment[response.appointment_id] = []
                # Use to_dict() without service_provider to avoid lazy loading
                responses_by_appointment[response.appointment_id].append(response.to_dict(include_service_provider=False))
            
            print(f"📊 Loaded {len(all_responses)} responses from appointment_responses table")
            
            # Update appointments mit neuen Responses
            for apt in simple_appointments:
                new_responses = responses_by_appointment.get(apt["id"], [])
                if new_responses:
                    apt["responses"] = json.dumps(new_responses)  # Für Kompatibilität als JSON String
                    apt["responses_array"] = new_responses  # Zusätzlich als Array
                    print(f"✅ Updated appointment {apt['id']} with {len(new_responses)} responses from new table")
                elif apt["responses"]:
                    print(f"📦 Using legacy JSON responses for appointment {apt['id']}")
        
        # Für Dienstleister: Filtere nur Termine, zu denen sie eingeladen wurden
        if current_user.user_role.value == "DIENSTLEISTER":
            filtered_appointments = []
            for apt in simple_appointments:
                try:
                    # Parse invited_service_providers JSON
                    invited_providers = []
                    if apt.get("invited_service_providers"):
                        if isinstance(apt["invited_service_providers"], str):
                            invited_providers = json.loads(apt["invited_service_providers"])
                        else:
                            invited_providers = apt["invited_service_providers"]
                    
                    # Prüfe ob der aktuelle Dienstleister eingeladen wurde
                    is_invited = any(
                        provider.get("id") == current_user.id 
                        for provider in invited_providers 
                        if isinstance(provider, dict)
                    )
                    
                    if is_invited:
                        filtered_appointments.append(apt)
                        print(f"✅ Dienstleister {current_user.id} ist zu Termin {apt['id']} eingeladen")
                    else:
                        print(f"⚠️ Dienstleister {current_user.id} ist NICHT zu Termin {apt['id']} eingeladen")
                        
                except Exception as e:
                    print(f"❌ Fehler beim Filtern von Termin {apt.get('id', 'unknown')}: {e}")
                    
            simple_appointments = filtered_appointments
            print(f"🔧 Nach Filterung: {len(simple_appointments)} relevante Termine für Dienstleister")
        
        print(f"✅ Successfully converted {len(simple_appointments)} appointments")
        return {"appointments": simple_appointments, "count": len(simple_appointments)}
        
    except Exception as e:
        print(f"❌ Error in get_my_appointments_simple: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return {"appointments": [], "count": 0, "error": str(e)}


@router.get("/follow-ups/pending", response_model=List[AppointmentResponse])
async def get_pending_follow_ups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Hole alle Termine, die ein Follow-up benötigen"""
    appointments = await AppointmentService.get_pending_follow_ups(db)
    return appointments


@router.get("/project/{project_id}", response_model=List[AppointmentResponse])
async def get_project_appointments(
    project_id: int,
    status: Optional[AppointmentStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Hole alle Termine eines Projekts - gefiltert nach Berechtigungen"""
    appointments = await AppointmentService.get_appointments_by_project(
        db=db,
        project_id=project_id,
        status=status
    )
    
    # Filtere Termine basierend auf Benutzerrolle und Berechtigungen
    filtered_appointments = []
    for appointment in appointments:
        if await _check_appointment_access(appointment, current_user):
            filtered_appointments.append(appointment)
    
    return filtered_appointments


# AB HIER: Parametrisierte Routes (müssen am Ende stehen!)

@router.post("/", response_model=AppointmentResponse)
async def create_appointment(
    appointment_data: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Erstelle einen neuen Besichtigungstermin"""
    try:
        appointment = await AppointmentService.create_appointment(
            db=db,
            appointment_data=appointment_data,
            created_by=current_user.id
        )
        return appointment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fehler beim Erstellen des Termins: {str(e)}"
        )


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Hole einen Termin nach ID - nur für berechtigte Benutzer"""
    appointment = await AppointmentService.get_appointment(db, appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Termin nicht gefunden"
        )
    
    # Berechtigungsprüfung
    if not await _check_appointment_access(appointment, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diesen Termin"
        )
    
    return appointment


@router.post("/{appointment_id}/respond")
async def respond_to_appointment(
    appointment_id: int,
    response_data: AppointmentResponseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Service Provider Antwort auf Termineinladung"""
    try:
        print(f"🔍 respond_to_appointment called:")
        print(f"  - appointment_id: {appointment_id}")
        print(f"  - current_user.id: {current_user.id}")
        print(f"  - response_data: {response_data}")
        print(f"  - response_data.status: {response_data.status}")
        print(f"  - response_data.message: {response_data.message}")
        print(f"  - response_data.suggested_date: {response_data.suggested_date}")
        
        # Prüfe ob Service Provider zu diesem Termin eingeladen ist
        print(f"🔍 Checking access for user {current_user.id} to appointment {appointment_id}")
        has_access = await AppointmentService.check_user_appointment_access(
            db=db,
            appointment_id=appointment_id,
            user=current_user
        )
        print(f"🔍 Access check result: {has_access}")
        
        if not has_access:
            print(f"❌ Access denied for user {current_user.id} to appointment {appointment_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sie sind nicht zu diesem Termin eingeladen"
            )
        
        print(f"✅ Access granted, calling AppointmentService.respond_to_appointment")
        appointment = await AppointmentService.respond_to_appointment(
            db=db,
            appointment_id=appointment_id,
            service_provider_id=current_user.id,
            status=response_data.status,
            message=response_data.message,
            suggested_date=response_data.suggested_date
        )
        print(f"✅ AppointmentService.respond_to_appointment completed successfully")
        return {"message": "Antwort erfolgreich gespeichert", "appointment": appointment}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fehler beim Speichern der Antwort: {str(e)}"
        )


@router.post("/{appointment_id}/complete", response_model=AppointmentResponse)
async def complete_inspection(
    appointment_id: int,
    decision_data: InspectionDecisionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Schließe Besichtigung ab und treffe Entscheidung"""
    try:
        appointment = await AppointmentService.complete_inspection(
            db=db,
            decision_data=decision_data,
            completed_by=current_user.id
        )
        return appointment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fehler beim Abschließen der Besichtigung: {str(e)}"
        )


@router.get("/{appointment_id}/calendar", response_model=CalendarEventData)
async def get_calendar_event(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generiere Kalendereintrag-Daten für .ics Download"""
    appointment = await AppointmentService.get_appointment(db, appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Termin nicht gefunden"
        )
    
    calendar_data = await AppointmentService.generate_calendar_event(appointment)
    return calendar_data


@router.get("/{appointment_id}/calendar/download")
async def download_calendar_event(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download .ics Kalendereintrag"""
    appointment = await AppointmentService.get_appointment(db, appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Termin nicht gefunden"
        )
    
    calendar_data = await AppointmentService.generate_calendar_event(appointment)
    
    # Generiere .ics Inhalt
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//BuildWise//Appointment System//EN
BEGIN:VEVENT
UID:{appointment_id}@buildwise.com
DTSTART:{calendar_data.start_date.strftime('%Y%m%dT%H%M%SZ')}
DTEND:{calendar_data.end_date.strftime('%Y%m%dT%H%M%SZ')}
SUMMARY:{calendar_data.title}
DESCRIPTION:{calendar_data.description}
LOCATION:{calendar_data.location}
ORGANIZER:MAILTO:{calendar_data.organizer}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""
    
    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename=appointment_{appointment_id}.ics"
        }
    )


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    update_data: AppointmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aktualisiere einen Termin"""
    appointment = await AppointmentService.get_appointment(db, appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Termin nicht gefunden"
        )
    
    # Aktualisiere nur die Felder, die gesetzt sind
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(appointment, field, value)
    
    appointment.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(appointment)
    
    return appointment


@router.delete("/{appointment_id}")
async def delete_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lösche einen Termin"""
    appointment = await AppointmentService.get_appointment(db, appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Termin nicht gefunden"
        )
    
    await db.delete(appointment)
    await db.commit()
    
    return {"message": "Termin erfolgreich gelöscht"}


@router.post("/{appointment_id}/follow-up-sent")
async def mark_follow_up_sent(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Markiere Follow-up Benachrichtigung als gesendet"""
    await AppointmentService.mark_follow_up_sent(db, appointment_id)
    return {"message": "Follow-up als gesendet markiert"} 


async def _check_appointment_access(appointment: AppointmentResponse, current_user: User) -> bool:
    """
    Prüft ob der aktuelle Benutzer Zugriff auf den Termin hat
    
    Berechtigt sind:
    - Bauträger: Termine die sie erstellt haben
    - Dienstleister: Nur Termine zu denen sie eingeladen wurden
    - Admin: Alle Termine
    """
    from ..models.user import UserRole
    
    # Admin hat immer Zugriff
    if current_user.user_role == UserRole.ADMIN:
        return True
    
    # Bauträger: Nur eigene Termine
    if current_user.user_role == UserRole.BAUTRAEGER:
        return appointment.created_by == current_user.id
    
    # Dienstleister: Nur eingeladene Termine
    if current_user.user_role == UserRole.DIENSTLEISTER:
        if appointment.invited_service_providers:
            invited_ids = [sp.id for sp in appointment.invited_service_providers]
            return current_user.id in invited_ids
        return False
    
    # Standardmäßig kein Zugriff
    return False 