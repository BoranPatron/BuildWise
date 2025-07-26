from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from ..models import Appointment, AppointmentStatus, AppointmentType, User, Project, Milestone, CostPosition, CostStatus
from ..schemas.appointment import (
    AppointmentCreate, AppointmentUpdate, ServiceProviderInvite, 
    InspectionDecisionRequest, CalendarEventData
)


class AppointmentService:
    """Service für die Verwaltung von Besichtigungsterminen"""
    
    @staticmethod
    async def create_appointment(
        db: AsyncSession, 
        appointment_data: AppointmentCreate, 
        created_by: int
    ) -> Appointment:
        """Erstelle einen neuen Besichtigungstermin"""
        try:
            print(f"🔧 Erstelle Appointment für Projekt {appointment_data.project_id}, Milestone {appointment_data.milestone_id}")
            
            # Lade Service Provider Informationen in einer effizienten Abfrage
            invited_providers = []
            if appointment_data.invited_service_provider_ids:
                print(f"📋 Lade {len(appointment_data.invited_service_provider_ids)} Service Provider")
                result = await db.execute(
                    select(User).where(User.id.in_(appointment_data.invited_service_provider_ids))
                )
                providers = result.scalars().all()
                
                invited_providers = [
                    {
                        "id": provider.id,
                        "email": provider.email,
                        "name": f"{provider.first_name} {provider.last_name}".strip(),
                        "status": "pending"
                    }
                    for provider in providers
                ]
                print(f"✅ {len(invited_providers)} Service Provider geladen")
            
            # Erstelle Appointment
            appointment = Appointment(
                project_id=appointment_data.project_id,
                milestone_id=appointment_data.milestone_id,
                created_by=created_by,
                title=appointment_data.title,
                description=appointment_data.description,
                appointment_type=appointment_data.appointment_type,
                scheduled_date=appointment_data.scheduled_date,
                duration_minutes=appointment_data.duration_minutes,
                location=appointment_data.location,
                location_details=appointment_data.location_details,
                invited_service_providers=invited_providers,
                status=AppointmentStatus.SCHEDULED,
                follow_up_notification_date=appointment_data.scheduled_date + timedelta(days=1)
            )
            
            print(f"💾 Speichere Appointment in Datenbank")
            db.add(appointment)
            await db.commit()
            await db.refresh(appointment)
            print(f"✅ Appointment {appointment.id} erfolgreich erstellt")
            
            # Führe zusätzliche Operationen asynchron aus, um Timeouts zu vermeiden
            if appointment_data.milestone_id:
                print(f"🔄 Setze Milestone {appointment_data.milestone_id} auf ON_HOLD")
                try:
                    await AppointmentService._set_milestone_on_hold(db, appointment_data.milestone_id)
                    await AppointmentService._mark_inspection_sent(db, appointment_data.milestone_id)
                    print(f"✅ Milestone-Operationen abgeschlossen")
                except Exception as e:
                    print(f"⚠️ Warnung bei Milestone-Operationen: {e}")
                    # Fahre trotz Fehler fort - Appointment wurde bereits erstellt
            
            return appointment
            
        except Exception as e:
            print(f"❌ Fehler beim Erstellen des Appointments: {e}")
            await db.rollback()
            raise e
    
    @staticmethod
    async def _set_milestone_on_hold(db: AsyncSession, milestone_id: int):
        """Setze alle CostPositions einer Milestone auf ON_HOLD"""
        try:
            print(f"🔄 Setze CostPositions für Milestone {milestone_id} auf ON_HOLD")
            result = await db.execute(
                select(CostPosition).where(CostPosition.milestone_id == milestone_id)
            )
            cost_positions = result.scalars().all()
            
            if cost_positions:
                for cost_position in cost_positions:
                    cost_position.status = CostStatus.ON_HOLD
                
                await db.commit()
                print(f"✅ {len(cost_positions)} CostPositions auf ON_HOLD gesetzt")
            else:
                print(f"ℹ️ Keine CostPositions für Milestone {milestone_id} gefunden")
                
        except Exception as e:
            print(f"❌ Fehler beim Setzen der CostPositions auf ON_HOLD: {e}")
            await db.rollback()
            raise e
    
    @staticmethod
    async def _mark_inspection_sent(db: AsyncSession, milestone_id: int):
        """Markiere Milestone als 'Besichtigung versendet'"""
        try:
            from ..models.milestone import Milestone
            from datetime import datetime
            
            print(f"🔄 Markiere Milestone {milestone_id} als 'Besichtigung versendet'")
            result = await db.execute(
                select(Milestone).where(Milestone.id == milestone_id)
            )
            milestone = result.scalar_one_or_none()
            
            if milestone:
                milestone.inspection_sent = True
                milestone.inspection_sent_at = datetime.utcnow()
                await db.commit()
                print(f"✅ Milestone {milestone_id} als 'Besichtigung versendet' markiert")
            else:
                print(f"⚠️ Milestone {milestone_id} nicht gefunden")
                
        except Exception as e:
            print(f"❌ Fehler beim Markieren der Milestone: {e}")
            await db.rollback()
            raise e
    
    @staticmethod
    async def get_appointment(db: AsyncSession, appointment_id: int) -> Optional[Appointment]:
        """Hole einen Termin nach ID"""
        result = await db.execute(
            select(Appointment)
            .options(
                selectinload(Appointment.project),
                selectinload(Appointment.milestone),
                selectinload(Appointment.creator),
                selectinload(Appointment.selected_service_provider)
            )
            .where(Appointment.id == appointment_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_appointments_by_project(
        db: AsyncSession, 
        project_id: int, 
        status: Optional[AppointmentStatus] = None
    ) -> List[Appointment]:
        """Hole alle Termine eines Projekts"""
        query = select(Appointment).options(
            selectinload(Appointment.project),
            selectinload(Appointment.milestone)
        ).where(Appointment.project_id == project_id)
        
        if status:
            query = query.where(Appointment.status == status)
        
        result = await db.execute(query.order_by(Appointment.scheduled_date.desc()))
        return result.scalars().all()

    @staticmethod
    async def get_appointments_for_user(
        db: AsyncSession, 
        user: User, 
        project_id: Optional[int] = None
    ) -> List[Appointment]:
        """
        Hole Termine basierend auf Benutzerrolle und Berechtigungen
        
        - Bauträger: Nur eigene erstellte Termine
        - Dienstleister: Nur Termine zu denen sie eingeladen wurden
        - Admin: Alle Termine
        """
        try:
            from ..models.user import UserRole
            
            print(f"🔍 get_appointments_for_user: user_id={user.id}, role={user.user_role}, project_id={project_id}")
            
            query = select(Appointment).options(
                selectinload(Appointment.project),
                selectinload(Appointment.milestone)
            )
            
            # Projektfilter falls angegeben
            if project_id:
                query = query.where(Appointment.project_id == project_id)
            
            # Rollenbasierte Filterung
            # Konvertiere user_role zu String für einheitlichen Vergleich
            user_role_str = user.user_role
            if hasattr(user.user_role, 'value'):
                user_role_str = user.user_role.value
            
            print(f"🔍 User Role String: '{user_role_str}' (type: {type(user.user_role)})")
            
            if user_role_str == "ADMIN":
                # Admin sieht alle Termine
                print(f"👑 Admin-Benutzer: Lade alle Termine")
                pass
            elif user_role_str == "BAUTRAEGER":
                # Bauträger sieht nur eigene Termine
                print(f"🏗️ Bauträger: Lade nur eigene Termine")
                query = query.where(Appointment.created_by == user.id)
            elif user_role_str == "DIENSTLEISTER":
                # Für Dienstleister: Hole alle Termine und filtere dann in Python
                # Das ist performanter als komplexe SQL-JSON-Abfragen
                print(f"🔧 Dienstleister: Lade alle Termine für Post-Processing")
                pass
            else:
                # Unbekannte Rolle - keine Termine
                print(f"⚠️ Unbekannte Benutzerrolle: {user_role_str}")
                query = query.where(False)
            
            result = await db.execute(query.order_by(Appointment.scheduled_date.desc()))
            appointments = result.scalars().all()
            print(f"📋 Gefunden: {len(appointments)} Termine")
            
            # Post-Processing für Dienstleister
            if user_role_str == "DIENSTLEISTER":
                print(f"🔍 Filtere Termine für Dienstleister {user.id}")
                filtered_appointments = []
                for appointment in appointments:
                    if appointment.invited_service_providers:
                        try:
                            # Parse JSON String zu Python-Objekt
                            if isinstance(appointment.invited_service_providers, str):
                                invited_providers = json.loads(appointment.invited_service_providers)
                            else:
                                invited_providers = appointment.invited_service_providers
                            
                            # Prüfe ob User eingeladen ist
                            if isinstance(invited_providers, list):
                                invited_ids = [provider.get('id') for provider in invited_providers if isinstance(provider, dict)]
                                if user.id in invited_ids:
                                    filtered_appointments.append(appointment)
                                    print(f"✅ Termin {appointment.id} für Dienstleister {user.id} verfügbar")
                        except (json.JSONDecodeError, AttributeError, TypeError) as e:
                            # Bei JSON-Fehlern: Termin überspringen
                            print(f"⚠️ JSON-Fehler bei Termin {appointment.id}: {e}")
                            continue
                
                print(f"✅ Gefiltert: {len(filtered_appointments)} Termine für Dienstleister {user.id}")
                return filtered_appointments
            
            print(f"✅ Rückgabe: {len(appointments)} Termine")
            return appointments
            
        except Exception as e:
            print(f"❌ Fehler in get_appointments_for_user: {e}")
            return []

    @staticmethod
    async def check_user_appointment_access(
        db: AsyncSession, 
        appointment_id: int, 
        user: User
    ) -> bool:
        """
        Prüft ob ein Benutzer Zugriff auf einen bestimmten Termin hat
        """
        from ..models.user import UserRole
        
        print(f"🔍 check_user_appointment_access:")
        print(f"  - appointment_id: {appointment_id}")
        print(f"  - user.id: {user.id}")
        print(f"  - user.user_role: {user.user_role}")
        
        appointment = await AppointmentService.get_appointment(db, appointment_id)
        if not appointment:
            print(f"❌ Appointment {appointment_id} not found")
            return False
        
        print(f"✅ Appointment found, invited_service_providers: {appointment.invited_service_providers}")
        
        # Admin hat immer Zugriff
        if user.user_role == UserRole.ADMIN:
            print(f"✅ Admin access granted")
            return True
        
        # Bauträger: Nur eigene Termine
        if user.user_role == UserRole.BAUTRAEGER:
            access = appointment.created_by == user.id
            print(f"🏗️ Bauträger access: {access} (created_by: {appointment.created_by})")
            return access
        
        # Dienstleister: Nur eingeladene Termine
        if user.user_role == UserRole.DIENSTLEISTER:
            print(f"🔧 Checking Dienstleister access")
            if appointment.invited_service_providers:
                # Parse JSON und prüfe ob User eingeladen ist
                try:
                    invited_providers = json.loads(appointment.invited_service_providers) if isinstance(appointment.invited_service_providers, str) else appointment.invited_service_providers
                    print(f"🔍 Parsed invited_providers: {invited_providers}")
                    if isinstance(invited_providers, list):
                        invited_ids = [provider.get('id') for provider in invited_providers if isinstance(provider, dict)]
                        print(f"🔍 Invited IDs: {invited_ids}")
                        access = user.id in invited_ids
                        print(f"🔧 Dienstleister access: {access}")
                        return access
                except (json.JSONDecodeError, AttributeError) as e:
                    print(f"❌ JSON parsing error: {e}")
                    pass
            print(f"❌ No invited_service_providers or user not in list")
            return False
        
        print(f"❌ Unknown user role or no access")
        return False
    
    @staticmethod
    async def get_pending_follow_ups(db: AsyncSession) -> List[Appointment]:
        """Hole alle Termine, die ein Follow-up benötigen"""
        now = datetime.utcnow()
        result = await db.execute(
            select(Appointment).where(
                and_(
                    Appointment.follow_up_notification_date <= now,
                    Appointment.follow_up_sent == False,
                    Appointment.inspection_completed == False,
                    Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
                )
            )
        )
        return result.scalars().all()
    
    @staticmethod
    async def respond_to_appointment(
        db: AsyncSession,
        appointment_id: int,
        service_provider_id: int,
        status: str,
        message: Optional[str] = None,
        suggested_date: Optional[datetime] = None
    ) -> Appointment:
        """Service Provider Antwort auf Termineinladung - Neue Version mit separater Response-Tabelle"""
        from app.models.appointment_response import AppointmentResponse
        from sqlalchemy import select
        
        print(f"🔍 AppointmentService.respond_to_appointment called (NEW VERSION):")
        print(f"  - appointment_id: {appointment_id}")
        print(f"  - service_provider_id: {service_provider_id}")
        print(f"  - status: {status}")
        print(f"  - message: {message}")
        print(f"  - suggested_date: {suggested_date}")
        
        # 1. Appointment laden
        appointment = await AppointmentService.get_appointment(db, appointment_id)
        if not appointment:
            print(f"❌ Appointment {appointment_id} not found")
            raise ValueError("Appointment not found")
        
        print(f"✅ Appointment {appointment_id} found")
        
        # 2. Bestehende Response suchen oder neue erstellen
        stmt = select(AppointmentResponse).where(
            AppointmentResponse.appointment_id == appointment_id,
            AppointmentResponse.service_provider_id == service_provider_id
        )
        result = await db.execute(stmt)
        existing_response = result.scalar_one_or_none()
        
        if existing_response:
            print(f"🔄 Updating existing response {existing_response.id}")
            # Update existing response
            existing_response.status = status
            existing_response.message = message
            existing_response.suggested_date = suggested_date
            existing_response.responded_at = datetime.utcnow()
            existing_response.updated_at = datetime.utcnow()
            response_record = existing_response
        else:
            print(f"✨ Creating new response")
            # Create new response
            response_record = AppointmentResponse(
                appointment_id=appointment_id,
                service_provider_id=service_provider_id,
                status=status,
                message=message,
                suggested_date=suggested_date,
                responded_at=datetime.utcnow()
            )
            db.add(response_record)
        
        # 4. Appointment Status aktualisieren basierend auf der neuen Antwort
        if status == "accepted":
            appointment.status = AppointmentStatus.ACCEPTED
            print(f"✅ Status set to ACCEPTED")
        elif status == "rejected":
            appointment.status = AppointmentStatus.REJECTED
            print(f"✅ Status set to REJECTED")
        elif status == "rejected_with_suggestion":
            appointment.status = AppointmentStatus.REJECTED_WITH_SUGGESTION
            print(f"✅ Status set to REJECTED_WITH_SUGGESTION")
        
        # 5. Änderungen speichern
        print(f"💾 Committing changes to database")
        await db.commit()
        await db.refresh(appointment)
        await db.refresh(response_record)
        print(f"✅ Database commit successful - Response ID: {response_record.id}")
        
        return appointment
    
    @staticmethod
    async def complete_inspection(
        db: AsyncSession,
        decision_data: InspectionDecisionRequest,
        completed_by: int
    ) -> Appointment:
        """Schließe Besichtigung ab und treffe Entscheidung"""
        appointment = await AppointmentService.get_appointment(db, decision_data.appointment_id)
        if not appointment:
            raise ValueError("Appointment not found")
        
        # Markiere Besichtigung als abgeschlossen
        appointment.inspection_completed = True
        appointment.selected_service_provider_id = decision_data.selected_service_provider_id
        appointment.inspection_notes = decision_data.inspection_notes
        appointment.requires_renegotiation = decision_data.requires_renegotiation
        appointment.renegotiation_details = decision_data.renegotiation_details
        appointment.status = AppointmentStatus.COMPLETED
        appointment.completed_at = datetime.utcnow()
        
        await db.commit()
        
        # Wenn keine Nachverhandlung erforderlich ist, aktiviere die CostPosition
        if not decision_data.requires_renegotiation:
            await AppointmentService._activate_selected_cost_position(
                db, 
                appointment.milestone_id, 
                decision_data.selected_service_provider_id
            )
        
        # Sende Absagen an nicht gewählte Service Provider
        await AppointmentService._send_rejections(db, appointment)
        
        return appointment
    
    @staticmethod
    async def _activate_selected_cost_position(
        db: AsyncSession, 
        milestone_id: int, 
        selected_service_provider_id: int
    ):
        """Aktiviere die CostPosition des gewählten Service Providers"""
        if not milestone_id:
            return
            
        result = await db.execute(
            select(CostPosition).where(
                and_(
                    CostPosition.milestone_id == milestone_id,
                    CostPosition.service_provider_id == selected_service_provider_id
                )
            )
        )
        cost_position = result.scalar_one_or_none()
        
        if cost_position:
            cost_position.status = CostStatus.ACTIVE
            await db.commit()
    
    @staticmethod
    async def _send_rejections(db: AsyncSession, appointment: Appointment):
        """Sende Absagen an nicht gewählte Service Provider"""
        # Hier würde normalerweise ein E-Mail-Service aufgerufen werden
        # Für jetzt markieren wir nur den Status
        pass
    
    @staticmethod
    async def generate_calendar_event(appointment: Appointment) -> CalendarEventData:
        """Generiere Kalendereintrag-Daten (.ics Format)"""
        end_date = appointment.scheduled_date + timedelta(minutes=appointment.duration_minutes)
        
        # Sammle E-Mail-Adressen der eingeladenen Service Provider
        attendees = []
        if appointment.invited_service_providers:
            attendees = [sp["email"] for sp in appointment.invited_service_providers]
        
        return CalendarEventData(
            title=appointment.title,
            description=appointment.description or "",
            start_date=appointment.scheduled_date,
            end_date=end_date,
            location=appointment.location or "",
            attendees=attendees,
            organizer=appointment.creator.email if appointment.creator else ""
        )
    
    @staticmethod
    async def mark_follow_up_sent(db: AsyncSession, appointment_id: int):
        """Markiere Follow-up Benachrichtigung als gesendet"""
        result = await db.execute(
            select(Appointment).where(Appointment.id == appointment_id)
        )
        appointment = result.scalar_one_or_none()
        
        if appointment:
            appointment.follow_up_sent = True
            await db.commit() 