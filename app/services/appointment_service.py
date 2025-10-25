from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from ..models import Appointment, AppointmentStatus, AppointmentType, User, Project, Milestone, CostPosition
from ..schemas.appointment import (
    AppointmentCreate, AppointmentUpdate, ServiceProviderInvite, 
    InspectionDecisionRequest, CalendarEventData
)
from ..services.notification_service import NotificationService


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
            print(f"[DEBUG] Erstelle Appointment für Projekt {appointment_data.project_id}, Milestone {appointment_data.milestone_id}")
            print(f"[INFO] DEBUG: Empfangene Kontaktdaten:")
            print(f"   - contact_person: '{appointment_data.contact_person}'")
            print(f"   - contact_phone: '{appointment_data.contact_phone}'") 
            print(f"   - preparation_notes: '{appointment_data.preparation_notes}'")
            
            # Lade Service Provider Informationen in einer effizienten Abfrage
            invited_providers = []
            if appointment_data.invited_service_provider_ids:
                print(f"[INFO] Lade {len(appointment_data.invited_service_provider_ids)} Service Provider")
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
                print(f"[SUCCESS] {len(invited_providers)} Service Provider geladen")
            
            # Erstelle Appointment
            print(f"[INFO] DEBUG: Erstelle Appointment-Objekt mit Kontaktdaten:")
            print(f"   - contact_person: '{appointment_data.contact_person}'")
            print(f"   - contact_phone: '{appointment_data.contact_phone}'") 
            print(f"   - preparation_notes: '{appointment_data.preparation_notes}'")
            
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
                # Erweiterte Besichtigungsdetails
                contact_person=appointment_data.contact_person,
                contact_phone=appointment_data.contact_phone,
                preparation_notes=appointment_data.preparation_notes,
                invited_service_providers=invited_providers,
                status=AppointmentStatus.SCHEDULED,
                follow_up_notification_date=appointment_data.scheduled_date + timedelta(days=1)
            )
            
            print(f"[DEBUG] DEBUG: Appointment-Objekt erstellt mit:")
            print(f"   - appointment.contact_person: '{appointment.contact_person}'")
            print(f"   - appointment.contact_phone: '{appointment.contact_phone}'") 
            print(f"   - appointment.preparation_notes: '{appointment.preparation_notes}'")
            
            print(f"[INFO] Speichere Appointment in Datenbank")
            db.add(appointment)
            await db.commit()
            await db.refresh(appointment)
            print(f"[SUCCESS] Appointment {appointment.id} erfolgreich erstellt")
            
            # Erstelle Benachrichtigungen für eingeladene Dienstleister (nur bei INSPECTION Terminen)
            print(f"[DEBUG] appointment_type: {appointment_data.appointment_type}, type: {type(appointment_data.appointment_type)}")
            print(f"[DEBUG] AppointmentType.INSPECTION: {AppointmentType.INSPECTION}, type: {type(AppointmentType.INSPECTION)}")
            print(f"[DEBUG] invited_service_provider_ids: {appointment_data.invited_service_provider_ids}")
            print(f"[DEBUG] appointment_type.value: {appointment_data.appointment_type.value}")
            print(f"[DEBUG] AppointmentType.INSPECTION.value: {AppointmentType.INSPECTION.value}")
            
            # Vergleiche die Enum-Werte statt der Enum-Objekte
            if (appointment_data.appointment_type.value == AppointmentType.INSPECTION.value and 
                appointment_data.invited_service_provider_ids):
                print(f"[NOTIFICATION] Erstelle Benachrichtigungen für {len(appointment_data.invited_service_provider_ids)} Dienstleister")
                try:
                    # Erstelle Benachrichtigungen direkt (ohne asyncio.create_task)
                    await AppointmentService._create_inspection_notifications(
                        db=db,
                        appointment=appointment,
                        invited_service_provider_ids=appointment_data.invited_service_provider_ids,
                        created_by=created_by
                    )
                    print(f"[SUCCESS] Benachrichtigungen für Besichtigungseinladungen erstellt")
                except Exception as e:
                    print(f"[WARNING] Fehler beim Erstellen der Benachrichtigungen: {e}")
                    # Fahre trotz Fehler fort - Appointment wurde bereits erstellt
            
            # Führe zusätzliche Operationen asynchron aus, um Timeouts zu vermeiden
            if appointment_data.milestone_id:
                print(f"[UPDATE] Setze Milestone {appointment_data.milestone_id} auf ON_HOLD")
                try:
                    await AppointmentService._set_milestone_on_hold(db, appointment_data.milestone_id)
                    await AppointmentService._mark_inspection_sent(db, appointment_data.milestone_id)
                    print(f"[SUCCESS] Milestone-Operationen abgeschlossen")
                except Exception as e:
                    print(f"[WARNING] Warnung bei Milestone-Operationen: {e}")
                    # Fahre trotz Fehler fort - Appointment wurde bereits erstellt
            
            return appointment
            
        except Exception as e:
            print(f"[ERROR] Fehler beim Erstellen des Appointments: {e}")
            await db.rollback()
            raise e
    
    @staticmethod
    async def _set_milestone_on_hold(db: AsyncSession, milestone_id: int):
        """Setze alle CostPositions einer Milestone auf ON_HOLD (Legacy-Funktion)"""
        try:
            print(f"[UPDATE] Setze CostPositions für Milestone {milestone_id} auf ON_HOLD")
            # Da wir jetzt einfache CostPosition für Rechnungen haben,
            # ist diese Funktion nicht mehr relevant
            print(f"ℹ️ CostPosition-Status nicht mehr relevant für neue Struktur")
        except Exception as e:
            print(f"[WARNING] Warnung beim Setzen der CostPosition-Status: {e}")
    
    @staticmethod
    async def _mark_inspection_sent(db: AsyncSession, milestone_id: int):
        """Markiere Milestone als Inspektion gesendet"""
        try:
            print(f"[UPDATE] Markiere Milestone {milestone_id} als Inspektion gesendet")
            result = await db.execute(
                select(Milestone).where(Milestone.id == milestone_id)
            )
            milestone = result.scalar_one_or_none()
            
            if milestone:
                milestone.inspection_sent = True
                milestone.inspection_sent_date = datetime.now()
                await db.commit()
                print(f"[SUCCESS] Milestone {milestone_id} als Inspektion gesendet markiert")
            else:
                print(f"[WARNING] Milestone {milestone_id} nicht gefunden")
                
        except Exception as e:
            print(f"[ERROR] Fehler beim Markieren der Inspektion: {e}")
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
            
            print(f"[DEBUG] get_appointments_for_user: user_id={user.id}, role={user.user_role}, project_id={project_id}")
            
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
            
            print(f"[DEBUG] User Role String: '{user_role_str}' (type: {type(user.user_role)})")
            
            if user_role_str == "ADMIN":
                # Admin sieht alle Termine
                print(f"👑 Admin-Benutzer: Lade alle Termine")
                pass
            elif user_role_str == "BAUTRAEGER":
                # Bauträger sieht nur eigene Termine
                print(f"[BUILD] Bauträger: Lade nur eigene Termine")
                query = query.where(Appointment.created_by == user.id)
            elif user_role_str == "DIENSTLEISTER":
                # Für Dienstleister: Hole alle Termine und filtere dann in Python
                # Das ist performanter als komplexe SQL-JSON-Abfragen
                print(f"[DEBUG] Dienstleister: Lade alle Termine für Post-Processing")
                pass
            else:
                # Unbekannte Rolle - keine Termine
                print(f"[WARNING] Unbekannte Benutzerrolle: {user_role_str}")
                query = query.where(False)
            
            result = await db.execute(query.order_by(Appointment.scheduled_date.desc()))
            appointments = result.scalars().all()
            print(f"[INFO] Gefunden: {len(appointments)} Termine")
            
            # Post-Processing für Dienstleister
            if user_role_str == "DIENSTLEISTER":
                print(f"[DEBUG] Filtere Termine für Dienstleister {user.id}")
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
                                    print(f"[SUCCESS] Termin {appointment.id} für Dienstleister {user.id} verfügbar")
                        except (json.JSONDecodeError, AttributeError, TypeError) as e:
                            # Bei JSON-Fehlern: Termin überspringen
                            print(f"[WARNING] JSON-Fehler bei Termin {appointment.id}: {e}")
                            continue
                
                print(f"[SUCCESS] Gefiltert: {len(filtered_appointments)} Termine für Dienstleister {user.id}")
                return filtered_appointments
            
            print(f"[SUCCESS] Rückgabe: {len(appointments)} Termine")
            return appointments
            
        except Exception as e:
            print(f"[ERROR] Fehler in get_appointments_for_user: {e}")
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
        
        print(f"[DEBUG] check_user_appointment_access:")
        print(f"  - appointment_id: {appointment_id}")
        print(f"  - user.id: {user.id}")
        print(f"  - user.user_role: {user.user_role}")
        
        appointment = await AppointmentService.get_appointment(db, appointment_id)
        if not appointment:
            print(f"[ERROR] Appointment {appointment_id} not found")
            return False
        
        print(f"[SUCCESS] Appointment found, invited_service_providers: {appointment.invited_service_providers}")
        
        # Admin hat immer Zugriff
        if user.user_role == UserRole.ADMIN:
            print(f"[SUCCESS] Admin access granted")
            return True
        
        # Bauträger: Nur eigene Termine
        if user.user_role == UserRole.BAUTRAEGER:
            access = appointment.created_by == user.id
            print(f"[BUILD] Bauträger access: {access} (created_by: {appointment.created_by})")
            return access
        
        # Dienstleister: Nur eingeladene Termine
        if user.user_role == UserRole.DIENSTLEISTER:
            print(f"[DEBUG] Checking Dienstleister access")
            if appointment.invited_service_providers:
                # Parse JSON und prüfe ob User eingeladen ist
                try:
                    invited_providers = json.loads(appointment.invited_service_providers) if isinstance(appointment.invited_service_providers, str) else appointment.invited_service_providers
                    print(f"[DEBUG] Parsed invited_providers: {invited_providers}")
                    if isinstance(invited_providers, list):
                        invited_ids = [provider.get('id') for provider in invited_providers if isinstance(provider, dict)]
                        print(f"[DEBUG] Invited IDs: {invited_ids}")
                        access = user.id in invited_ids
                        print(f"[DEBUG] Dienstleister access: {access}")
                        return access
                except (json.JSONDecodeError, AttributeError) as e:
                    print(f"[ERROR] JSON parsing error: {e}")
                    pass
            print(f"[ERROR] No invited_service_providers or user not in list")
            return False
        
        print(f"[ERROR] Unknown user role or no access")
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
        from app.models.notification import Notification, NotificationType, NotificationPriority
        from sqlalchemy import select
        
        print(f"[DEBUG] AppointmentService.respond_to_appointment called (NEW VERSION):")
        print(f"  - appointment_id: {appointment_id}")
        print(f"  - service_provider_id: {service_provider_id}")
        print(f"  - status: {status}")
        print(f"  - message: {message}")
        print(f"  - suggested_date: {suggested_date}")
        
        # 1. Appointment laden
        appointment = await AppointmentService.get_appointment(db, appointment_id)
        if not appointment:
            print(f"[ERROR] Appointment {appointment_id} not found")
            raise ValueError("Appointment not found")
        
        print(f"[SUCCESS] Appointment {appointment_id} found")
        
        # 2. Service Provider laden für Benachrichtigung
        service_provider = None
        service_provider_name = "Dienstleister"
        if service_provider_id:
            sp_result = await db.execute(
                select(User).where(User.id == service_provider_id)
            )
            service_provider = sp_result.scalar_one_or_none()
            if service_provider:
                if service_provider.company_name:
                    service_provider_name = service_provider.company_name
                else:
                    service_provider_name = f"{service_provider.first_name or ''} {service_provider.last_name or ''}".strip()
                    if not service_provider_name:
                        service_provider_name = f"Dienstleister #{service_provider.id}"
        
        # 3. Bestehende Response suchen oder neue erstellen
        stmt = select(AppointmentResponse).where(
            AppointmentResponse.appointment_id == appointment_id,
            AppointmentResponse.service_provider_id == service_provider_id
        )
        result = await db.execute(stmt)
        existing_response = result.scalar_one_or_none()
        
        if existing_response:
            print(f"[UPDATE] Updating existing response {existing_response.id}")
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
            print(f"[SUCCESS] Status set to ACCEPTED")
        elif status == "rejected":
            appointment.status = AppointmentStatus.REJECTED
            print(f"[SUCCESS] Status set to REJECTED")
        elif status == "rejected_with_suggestion":
            appointment.status = AppointmentStatus.REJECTED_WITH_SUGGESTION
            print(f"[SUCCESS] Status set to REJECTED_WITH_SUGGESTION")
        
        # 5. Änderungen speichern
        print(f"[INFO] Committing changes to database")
        await db.commit()
        await db.refresh(appointment)
        await db.refresh(response_record)
        print(f"[SUCCESS] Database commit successful - Response ID: {response_record.id}")
        
        # 6. Benachrichtigung an Bauträger erstellen
        try:
            print(f"📧 Creating notification for Bauträger (created_by: {appointment.created_by})")
            
            # Erstelle Status-Text
            if status == "accepted":
                status_text = "zugesagt"
                priority = NotificationPriority.HIGH
                notification_type = NotificationType.APPOINTMENT_RESPONSE
            elif status == "rejected":
                status_text = "abgelehnt"
                priority = NotificationPriority.NORMAL
                notification_type = NotificationType.APPOINTMENT_RESPONSE
            elif status == "rejected_with_suggestion":
                status_text = "einen Alternativtermin vorgeschlagen"
                priority = NotificationPriority.HIGH
                notification_type = NotificationType.APPOINTMENT_RESPONSE
            else:
                status_text = "geantwortet"
                priority = NotificationPriority.NORMAL
                notification_type = NotificationType.APPOINTMENT_RESPONSE
            
            # Erstelle Notification-Daten
            notification_data = {
                "appointment_id": appointment.id,
                "appointment_title": appointment.title,
                "scheduled_date": appointment.scheduled_date.isoformat(),
                "location": appointment.location or "",
                "service_provider_name": service_provider_name,
                "response_status": status,
                "response_message": message or "",
                "suggested_date": suggested_date.isoformat() if suggested_date else None
            }
            
            # Erstelle Benachrichtigung
            notification = Notification(
                recipient_id=appointment.created_by,
                type=notification_type,
                priority=priority,
                title=f"Terminantwort: {appointment.title}",
                message=f"{service_provider_name} hat dem Besichtigungstermin \"{appointment.title}\" {status_text}.",
                data=json.dumps(notification_data),
                related_appointment_id=appointment.id,
                related_project_id=appointment.project_id,
                related_milestone_id=appointment.milestone_id
            )
            
            db.add(notification)
            await db.commit()
            await db.refresh(notification)
            print(f"✅ Notification {notification.id} created for Bauträger {appointment.created_by}")
            
        except Exception as e:
            print(f"❌ Error creating notification for Bauträger: {e}")
            # Fehler bei Benachrichtigung soll den Hauptprozess nicht stoppen
            import traceback
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
        
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
            cost_position.status = "active" # Da CostStatus nicht mehr existiert, verwende String
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
    
    @staticmethod
    async def _create_inspection_notifications(
        db: AsyncSession,
        appointment: Appointment,
        invited_service_provider_ids: List[int],
        created_by: int
    ):
        """
        Erstellt Benachrichtigungen für eingeladene Dienstleister bei Besichtigungsterminen
        
        Args:
            db: Datenbank-Session
            appointment: Das erstellte Appointment
            invited_service_provider_ids: Liste der eingeladenen Dienstleister-IDs
            created_by: ID des Bauträgers, der die Besichtigung erstellt hat
        """
        try:
            # Lade Bauträger-Informationen
            bautraeger_result = await db.execute(
                select(User).where(User.id == created_by)
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
            
            # Lade Projekt- und Milestone-Informationen
            project_name = "Unbekanntes Projekt"
            milestone_title = "Unbekanntes Gewerk"
            
            if appointment.project_id:
                project_result = await db.execute(
                    select(Project).where(Project.id == appointment.project_id)
                )
                project = project_result.scalar_one_or_none()
                if project:
                    project_name = project.name
            
            if appointment.milestone_id:
                milestone_result = await db.execute(
                    select(Milestone).where(Milestone.id == appointment.milestone_id)
                )
                milestone = milestone_result.scalar_one_or_none()
                if milestone:
                    milestone_title = milestone.title
            
            # Datum und Zeit formatieren
            scheduled_date_str = appointment.scheduled_date.strftime('%d.%m.%Y') if appointment.scheduled_date else "Termin folgt"
            time_info = ""
            if appointment.scheduled_date:
                # Extrahiere Zeit aus scheduled_date (falls es ein datetime ist)
                if hasattr(appointment.scheduled_date, 'time'):
                    time_str = appointment.scheduled_date.time().strftime('%H:%M')
                    time_info = f" um {time_str}"
            
            # Ort-Informationen
            location_info = ""
            if appointment.location:
                location_info = f" Ort: {appointment.location}"
            
            # Erstelle Benachrichtigungen für jeden eingeladenen Dienstleister
            for service_provider_id in invited_service_provider_ids:
                try:
                    # Erstelle Benachrichtigungsdaten
                    notification_data = {
                        "appointment_id": appointment.id,
                        "milestone_id": appointment.milestone_id,
                        "milestone_title": milestone_title,
                        "project_id": appointment.project_id,
                        "project_name": project_name,
                        "bautraeger_id": created_by,
                        "bautraeger_name": bautraeger_name,
                        "service_provider_id": service_provider_id,
                        "scheduled_date": appointment.scheduled_date.isoformat() if appointment.scheduled_date else None,
                        "location": appointment.location,
                        "contact_person": appointment.contact_person,
                        "contact_phone": appointment.contact_phone,
                        "preparation_notes": appointment.preparation_notes,
                        "direct_link": f"/project/{appointment.project_id}/milestone/{appointment.milestone_id}",
                        "tradeId": appointment.milestone_id,  # Für Frontend-Kompatibilität
                        "tradeTitle": milestone_title,  # Für Frontend-Kompatibilität
                        "projectName": project_name  # Für Frontend-Kompatibilität
                    }
                    
                    # Erstelle Benachrichtigung
                    from ..models.notification import Notification, NotificationType, NotificationPriority
                    
                    notification = Notification(
                        recipient_id=service_provider_id,
                        type=NotificationType.TENDER_INVITATION,  # Verwende existierenden Enum-Wert
                        priority=NotificationPriority.HIGH,
                        title=f"Einladung zur Besichtigung: {milestone_title}",
                        message=f"{bautraeger_name} hat dich zur Besichtigung für '{milestone_title}' im Projekt '{project_name}' eingeladen. Termin: {scheduled_date_str}{time_info}{location_info}",
                        data=json.dumps(notification_data),
                        related_milestone_id=appointment.milestone_id,
                        related_project_id=appointment.project_id,
                        is_read=False,
                        is_acknowledged=False,
                        created_at=datetime.utcnow()
                    )
                    
                    db.add(notification)
                    print(f"[SUCCESS] Benachrichtigung für Service Provider {service_provider_id} erstellt")
                    
                except Exception as e:
                    print(f"[WARNING] Fehler beim Erstellen der Benachrichtigung für Service Provider {service_provider_id}: {e}")
                    continue
            
            # Commit alle Benachrichtigungen
            await db.commit()
            print(f"[SUCCESS] Alle Benachrichtigungen für Besichtigungseinladung erstellt")
            
        except Exception as e:
            print(f"[ERROR] Fehler beim Erstellen der Besichtigungseinladungs-Benachrichtigungen: {e}")
            await db.rollback()
            raise e 