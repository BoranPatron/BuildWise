from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import json

from ..models import (
    Acceptance, AcceptanceDefect, AcceptanceStatus, AcceptanceType, DefectSeverity,
    Milestone, Project, User, Appointment, AppointmentType, AppointmentStatus
)
from ..schemas.acceptance import (
    AcceptanceCreate, AcceptanceUpdate, AcceptanceResponse,
    AcceptanceDefectCreate, AcceptanceDefectUpdate,
    AcceptanceScheduleRequest, AcceptanceScheduleResponse,
    AcceptanceCompleteRequest, AcceptanceSummary, AcceptanceListItem
)
from .appointment_service import AppointmentService
from .pdf_service import PDFService
from .defect_task_service import process_acceptance_completion


class AcceptanceService:
    """Service für die Verwaltung von Abnahme-Workflows"""
    
    @staticmethod
    async def create_acceptance(
        db: AsyncSession, 
        acceptance_data: AcceptanceCreate, 
        contractor_id: int
    ) -> Acceptance:
        """Erstelle eine neue Abnahme"""
        try:
            print(f"[DEBUG] Erstelle Abnahme für Milestone {acceptance_data.milestone_id}")
            
            # Prüfe ob Milestone existiert und completion_status = 'completion_requested'
            milestone_result = await db.execute(
                select(Milestone).where(Milestone.id == acceptance_data.milestone_id)
            )
            milestone = milestone_result.scalar_one_or_none()
            
            if not milestone:
                raise ValueError(f"Milestone {acceptance_data.milestone_id} nicht gefunden")
            
            if milestone.completion_status != 'completion_requested':
                raise ValueError(f"Milestone muss completion_status 'completion_requested' haben, ist aber '{milestone.completion_status}'")
            
            # Erstelle Abnahme
            acceptance = Acceptance(
                project_id=acceptance_data.project_id,
                milestone_id=acceptance_data.milestone_id,
                contractor_id=contractor_id,
                service_provider_id=acceptance_data.service_provider_id,
                created_by=contractor_id,
                appointment_id=acceptance_data.appointment_id,
                acceptance_type=acceptance_data.acceptance_type,
                scheduled_date=acceptance_data.scheduled_date,
                acceptance_notes=acceptance_data.acceptance_notes,
                contractor_notes=acceptance_data.contractor_notes,
                service_provider_notes=acceptance_data.service_provider_notes,
                quality_rating=acceptance_data.quality_rating,
                timeliness_rating=acceptance_data.timeliness_rating,
                overall_rating=acceptance_data.overall_rating,
                photos=acceptance_data.photos or [],
                documents=acceptance_data.documents or [],
                warranty_period_months=acceptance_data.warranty_period_months,
                status=AcceptanceStatus.SCHEDULED
            )
            
            db.add(acceptance)
            await db.commit()
            await db.refresh(acceptance)
            
            # Update Milestone Status
            milestone.completion_status = 'under_review'
            await db.commit()
            
            print(f"[SUCCESS] Abnahme {acceptance.id} erstellt")
            return acceptance
            
        except Exception as e:
            await db.rollback()
            print(f"[ERROR] Fehler beim Erstellen der Abnahme: {e}")
            raise


    @staticmethod
    async def schedule_acceptance_appointment(
        db: AsyncSession,
        milestone_id: int,
        contractor_id: int,
        service_provider_id: int,
        proposed_date: datetime,
        notes: Optional[str] = None
    ) -> Appointment:
        """Erstelle einen Abnahme-Termin (analog zu Besichtigungsterminen)"""
        try:
            print(f"[INFO] Erstelle Abnahme-Termin für Milestone {milestone_id}")
            
            # Lade Milestone und Project
            milestone_result = await db.execute(
                select(Milestone).options(selectinload(Milestone.project))
                .where(Milestone.id == milestone_id)
            )
            milestone = milestone_result.scalar_one_or_none()
            
            if not milestone:
                raise ValueError(f"Milestone {milestone_id} nicht gefunden")
            
            # Erstelle Appointment für Abnahme
            appointment = Appointment(
                project_id=milestone.project_id,
                milestone_id=milestone_id,
                created_by=contractor_id,
                title=f"Abnahme: {milestone.title}",
                description=f"Abnahme-Termin für das Gewerk '{milestone.title}'. {notes or ''}",
                appointment_type=AppointmentType.ACCEPTANCE,
                status=AppointmentStatus.PENDING_RESPONSE,
                scheduled_date=proposed_date,
                duration_minutes=120,  # Standard: 2 Stunden für Abnahme
                location=milestone.project.address if milestone.project else None,
                invited_service_providers=[{
                    "id": service_provider_id,
                    "status": "pending"
                }]
            )
            
            db.add(appointment)
            await db.commit()
            await db.refresh(appointment)
            
            # TODO: Sende Benachrichtigung an Dienstleister
            print(f"📧 Benachrichtigung an Dienstleister {service_provider_id} über Abnahme-Termin {appointment.id}")
            
            print(f"[SUCCESS] Abnahme-Termin {appointment.id} erstellt")
            return appointment
            
        except Exception as e:
            await db.rollback()
            print(f"[ERROR] Fehler beim Erstellen des Abnahme-Termins: {e}")
            raise


    @staticmethod
    async def respond_to_acceptance_appointment(
        db: AsyncSession,
        appointment_id: int,
        service_provider_id: int,
        accepted: bool,
        message: Optional[str] = None,
        counter_proposal: Optional[datetime] = None
    ) -> Appointment:
        """Antwort auf Abnahme-Terminvorschlag"""
        try:
            print(f"[INFO] Antwort auf Abnahme-Termin {appointment_id}: {'Akzeptiert' if accepted else 'Abgelehnt'}")
            
            # Lade Appointment
            appointment_result = await db.execute(
                select(Appointment).where(Appointment.id == appointment_id)
            )
            appointment = appointment_result.scalar_one_or_none()
            
            if not appointment:
                raise ValueError(f"Appointment {appointment_id} nicht gefunden")
            
            if appointment.appointment_type != AppointmentType.ACCEPTANCE:
                raise ValueError("Dies ist kein Abnahme-Termin")
            
            # Update Responses
            responses = appointment.responses or []
            
            # Entferne alte Antwort des Service Providers
            responses = [r for r in responses if r.get('service_provider_id') != service_provider_id]
            
            # Füge neue Antwort hinzu
            response_data = {
                "service_provider_id": service_provider_id,
                "status": "accepted" if accepted else "rejected",
                "message": message,
                "responded_at": datetime.utcnow().isoformat()
            }
            
            if counter_proposal:
                response_data["suggested_date"] = counter_proposal.isoformat()
                appointment.status = AppointmentStatus.REJECTED_WITH_SUGGESTION
            elif accepted:
                appointment.status = AppointmentStatus.ACCEPTED
            else:
                appointment.status = AppointmentStatus.REJECTED
            
            responses.append(response_data)
            appointment.responses = responses
            
            await db.commit()
            
            # TODO: Sende Benachrichtigung an Bauträger
            print(f"📧 Benachrichtigung an Bauträger über Antwort von Dienstleister {service_provider_id}: {'Akzeptiert' if accepted else 'Abgelehnt'}")
            
            print(f"[SUCCESS] Antwort auf Abnahme-Termin gespeichert")
            return appointment
            
        except Exception as e:
            await db.rollback()
            print(f"[ERROR] Fehler bei Antwort auf Abnahme-Termin: {e}")
            raise


    @staticmethod
    async def start_acceptance(
        db: AsyncSession,
        acceptance_id: int,
        user_id: int
    ) -> Acceptance:
        """Starte die Abnahme"""
        try:
            print(f"[INFO] Starte Abnahme {acceptance_id}")
            
            acceptance_result = await db.execute(
                select(Acceptance).where(Acceptance.id == acceptance_id)
            )
            acceptance = acceptance_result.scalar_one_or_none()
            
            if not acceptance:
                raise ValueError(f"Abnahme {acceptance_id} nicht gefunden")
            
            if acceptance.status != AcceptanceStatus.SCHEDULED:
                raise ValueError(f"Abnahme hat falschen Status: {acceptance.status}")
            
            # Update Status und Zeitstempel
            acceptance.status = AcceptanceStatus.IN_PROGRESS
            acceptance.started_at = datetime.utcnow()
            
            await db.commit()
            
            print(f"[SUCCESS] Abnahme {acceptance_id} gestartet")
            return acceptance
            
        except Exception as e:
            await db.rollback()
            print(f"[ERROR] Fehler beim Starten der Abnahme: {e}")
            raise








    @staticmethod
    async def get_acceptance_by_id(
        db: AsyncSession,
        acceptance_id: int,
        user_id: int
    ) -> Optional[Acceptance]:
        """Lade Abnahme mit allen Details"""
        try:
            result = await db.execute(
                select(Acceptance)
                .options(
                    selectinload(Acceptance.project),
                    selectinload(Acceptance.milestone),
                    selectinload(Acceptance.contractor),
                    selectinload(Acceptance.service_provider),
                    selectinload(Acceptance.defects),
                    selectinload(Acceptance.appointment)
                )
                .where(Acceptance.id == acceptance_id)
            )
            
            acceptance = result.scalar_one_or_none()
            
            # Prüfe Berechtigung
            if acceptance and (
                acceptance.contractor_id == user_id or 
                acceptance.service_provider_id == user_id or
                acceptance.created_by == user_id
            ):
                return acceptance
            
            return None
            
        except Exception as e:
            print(f"[ERROR] Fehler beim Laden der Abnahme: {e}")
            return None


    @staticmethod
    async def get_acceptances_for_user(
        db: AsyncSession,
        user_id: int,
        status: Optional[AcceptanceStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Acceptance]:
        """Lade Abnahmen für einen Benutzer"""
        try:
            query = select(Acceptance).options(
                selectinload(Acceptance.project),
                selectinload(Acceptance.milestone),
                selectinload(Acceptance.contractor),
                selectinload(Acceptance.service_provider)
            ).where(
                or_(
                    Acceptance.contractor_id == user_id,
                    Acceptance.service_provider_id == user_id,
                    Acceptance.created_by == user_id
                )
            )
            
            if status:
                query = query.where(Acceptance.status == status)
            
            query = query.order_by(desc(Acceptance.created_at)).limit(limit).offset(offset)
            
            result = await db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            print(f"[ERROR] Fehler beim Laden der Abnahmen: {e}")
            return []


    @staticmethod
    async def get_acceptance_summary(
        db: AsyncSession,
        user_id: int
    ) -> AcceptanceSummary:
        """Erstelle Abnahme-Zusammenfassung für Dashboard"""
        try:
            # Basis-Query für Benutzer
            base_query = select(Acceptance).where(
                or_(
                    Acceptance.contractor_id == user_id,
                    Acceptance.service_provider_id == user_id,
                    Acceptance.created_by == user_id
                )
            )
            
            # Gesamtanzahl
            total_result = await db.execute(
                select(func.count(Acceptance.id)).where(
                    or_(
                        Acceptance.contractor_id == user_id,
                        Acceptance.service_provider_id == user_id,
                        Acceptance.created_by == user_id
                    )
                )
            )
            total_acceptances = total_result.scalar() or 0
            
            # Ausstehende Abnahmen
            pending_result = await db.execute(
                select(func.count(Acceptance.id)).where(
                    and_(
                        or_(
                            Acceptance.contractor_id == user_id,
                            Acceptance.service_provider_id == user_id,
                            Acceptance.created_by == user_id
                        ),
                        Acceptance.status.in_([
                            AcceptanceStatus.SCHEDULED,
                            AcceptanceStatus.IN_PROGRESS
                        ])
                    )
                )
            )
            pending_acceptances = pending_result.scalar() or 0
            
            # Abgeschlossene Abnahmen
            completed_result = await db.execute(
                select(func.count(Acceptance.id)).where(
                    and_(
                        or_(
                            Acceptance.contractor_id == user_id,
                            Acceptance.service_provider_id == user_id,
                            Acceptance.created_by == user_id
                        ),
                        Acceptance.status.in_([
                            AcceptanceStatus.ACCEPTED,
                            AcceptanceStatus.ACCEPTED_WITH_DEFECTS,
                            AcceptanceStatus.REJECTED
                        ])
                    )
                )
            )
            completed_acceptances = completed_result.scalar() or 0
            
            # Akzeptierte
            accepted_result = await db.execute(
                select(func.count(Acceptance.id)).where(
                    and_(
                        or_(
                            Acceptance.contractor_id == user_id,
                            Acceptance.service_provider_id == user_id,
                            Acceptance.created_by == user_id
                        ),
                        Acceptance.status.in_([
                            AcceptanceStatus.ACCEPTED,
                            AcceptanceStatus.ACCEPTED_WITH_DEFECTS
                        ])
                    )
                )
            )
            accepted_count = accepted_result.scalar() or 0
            
            # Abgelehnte
            rejected_result = await db.execute(
                select(func.count(Acceptance.id)).where(
                    and_(
                        or_(
                            Acceptance.contractor_id == user_id,
                            Acceptance.service_provider_id == user_id,
                            Acceptance.created_by == user_id
                        ),
                        Acceptance.status == AcceptanceStatus.REJECTED
                    )
                )
            )
            rejected_count = rejected_result.scalar() or 0
            
            # Mängel
            defects_result = await db.execute(
                select(func.count(AcceptanceDefect.id))
                .join(Acceptance)
                .where(
                    or_(
                        Acceptance.contractor_id == user_id,
                        Acceptance.service_provider_id == user_id,
                        Acceptance.created_by == user_id
                    )
                )
            )
            defects_count = defects_result.scalar() or 0
            
            # Durchschnittsbewertung
            rating_result = await db.execute(
                select(func.avg(Acceptance.overall_rating)).where(
                    and_(
                        or_(
                            Acceptance.contractor_id == user_id,
                            Acceptance.service_provider_id == user_id,
                            Acceptance.created_by == user_id
                        ),
                        Acceptance.overall_rating.isnot(None)
                    )
                )
            )
            average_rating = rating_result.scalar()
            
            return AcceptanceSummary(
                total_acceptances=total_acceptances,
                pending_acceptances=pending_acceptances,
                completed_acceptances=completed_acceptances,
                accepted_count=accepted_count,
                rejected_count=rejected_count,
                defects_count=defects_count,
                average_rating=float(average_rating) if average_rating else None
            )
            
        except Exception as e:
            print(f"[ERROR] Fehler bei Abnahme-Zusammenfassung: {e}")
            return AcceptanceSummary(
                total_acceptances=0,
                pending_acceptances=0,
                completed_acceptances=0,
                accepted_count=0,
                rejected_count=0,
                defects_count=0,
                average_rating=None
            )


    @staticmethod
    async def complete_acceptance(
        db: AsyncSession,
        acceptance_id: Optional[int],
        completion_data: dict,
        completed_by_user_id: int
    ) -> Acceptance:
        """
        Schließt eine Abnahme ab und erstellt automatisch Tasks für Mängel
        
        Args:
            db: Database Session
            acceptance_id: ID der Abnahme
            completion_data: Abnahme-Daten (accepted, defects, etc.)
            completed_by_user_id: User-ID des Bauträgers
        
        Returns:
            Acceptance: Die abgeschlossene Abnahme
        """
        try:
            if acceptance_id:
                print(f"🏁 Schließe bestehende Abnahme {acceptance_id} ab...")
                
                # Hole bestehende Abnahme
                result = await db.execute(
                    select(Acceptance)
                    .options(selectinload(Acceptance.defects))
                    .where(Acceptance.id == acceptance_id)
                )
                acceptance = result.scalars().first()
                
                if not acceptance:
                    raise ValueError(f"Abnahme {acceptance_id} nicht gefunden")
            else:
                print(f"🏁 Erstelle neue Abnahme für Milestone {completion_data.get('milestone_id')}...")
                
                # Erstelle neue Abnahme
                milestone_id = completion_data.get('milestone_id')
                if not milestone_id:
                    raise ValueError("milestone_id ist erforderlich für neue Abnahme")
                
                # Hole Milestone-Daten
                milestone_result = await db.execute(
                    select(Milestone).where(Milestone.id == milestone_id)
                )
                milestone = milestone_result.scalar_one_or_none()
                if not milestone:
                    raise ValueError(f"Milestone {milestone_id} nicht gefunden")
                
                # Ermittle Service Provider aus akzeptiertem Quote oder Milestone
                service_provider_id = None
                
                # Versuch 1: Suche nach akzeptiertem Quote
                from ..models.quote import Quote, QuoteStatus
                quotes_result = await db.execute(
                    select(Quote).where(
                        and_(
                            Quote.milestone_id == milestone_id,
                            Quote.status == QuoteStatus.ACCEPTED
                        )
                    )
                )
                accepted_quote = quotes_result.scalar_one_or_none()
                if accepted_quote:
                    service_provider_id = accepted_quote.service_provider_id
                    print(f"[SUCCESS] Service Provider aus akzeptiertem Quote ermittelt: {service_provider_id}")
                
                # Versuch 2: Verwende milestone.accepted_by (für Bauträger-Workflow)
                elif milestone.accepted_by:
                    service_provider_id = milestone.accepted_by
                    print(f"[SUCCESS] Service Provider aus milestone.accepted_by ermittelt: {service_provider_id}")
                
                # Fallback: Verwende den Bauträger als Service Provider (für reine Bauträger-Abnahmen)
                else:
                    print(f"[WARNING] Kein Service Provider für Milestone {milestone_id} gefunden - verwende Bauträger als Fallback")
                    service_provider_id = completed_by_user_id  # Bauträger führt selbst die Abnahme durch
                
                # Erstelle neue Abnahme
                acceptance = Acceptance(
                    project_id=milestone.project_id,
                    milestone_id=milestone_id,
                    contractor_id=completed_by_user_id,
                    service_provider_id=service_provider_id,
                    created_by=completed_by_user_id,
                    acceptance_type=AcceptanceType.FINAL,
                    status=AcceptanceStatus.ACCEPTED,  # Wird später basierend auf acceptance.accepted gesetzt
                    completed_at=datetime.now()
                )
                db.add(acceptance)
                await db.flush()  # Um ID zu erhalten
            
            # Aktualisiere Abnahme-Status basierend auf Ergebnis
            acceptance.accepted = completion_data.get('accepted', False)
            if acceptance.accepted:
                acceptance.status = AcceptanceStatus.ACCEPTED
            else:
                acceptance.status = AcceptanceStatus.ACCEPTED_WITH_DEFECTS
            acceptance.completed_at = datetime.now()
            acceptance.acceptance_notes = completion_data.get('acceptanceNotes', '')
            acceptance.contractor_notes = completion_data.get('contractorNotes', '')
            acceptance.quality_rating = completion_data.get('qualityRating', 0)
            acceptance.timeliness_rating = completion_data.get('timelinessRating', 0)
            acceptance.overall_rating = completion_data.get('overallRating', 0)
            acceptance.photos = completion_data.get('photos', [])
            acceptance.checklist_data = completion_data.get('checklist', {})
            
            # Bei Abnahme unter Vorbehalt
            if not acceptance.accepted:
                acceptance.review_date = datetime.strptime(completion_data.get('reviewDate', ''), '%Y-%m-%d').date() if completion_data.get('reviewDate') else None
                acceptance.review_notes = completion_data.get('reviewNotes', '')
            
            # Erstelle/Aktualisiere Mängel
            defects_data = completion_data.get('defects', [])
            for defect_data in defects_data:
                defect = AcceptanceDefect(
                    acceptance_id=acceptance.id,
                    title=defect_data.get('title', ''),
                    description=defect_data.get('description', ''),
                    severity=DefectSeverity(defect_data.get('severity', 'MINOR')),
                    location=defect_data.get('location', ''),
                    room=defect_data.get('room', ''),
                    photos=defect_data.get('photos', []),
                    resolved=False
                )
                db.add(defect)
                # Nicht acceptance.defects.append(defect) verwenden - das verursacht lazy loading
            
            await db.commit()
            
            # Lade Acceptance mit Defects neu
            acceptance_result = await db.execute(
                select(Acceptance)
                .options(selectinload(Acceptance.defects))
                .where(Acceptance.id == acceptance.id)
            )
            acceptance = acceptance_result.scalars().first()
            
            # Aktualisiere Milestone-Status ZUERST (vor Task-Erstellung)
            if acceptance.milestone_id:
                milestone_result = await db.execute(select(Milestone).where(Milestone.id == acceptance.milestone_id))
                milestone = milestone_result.scalars().first()
                
                if milestone:
                    if acceptance.accepted:
                        milestone.completion_status = 'completed'
                        milestone.status = 'completed'
                        milestone.completed_at = datetime.now()
                        print(f"[SUCCESS] Milestone {milestone.title} als abgenommen markiert")
                        
                        # Sende Benachrichtigung an den Dienstleister über die finale Abnahme
                        try:
                            from .notification_service import NotificationService
                            await NotificationService.create_milestone_completed_notification(db, milestone.id)
                        except Exception as e:
                            print(f"[WARNING] Fehler beim Erstellen der Abnahme-Benachrichtigung: {e}")
                            # Fehler bei Benachrichtigung sollte nicht die Abnahme blockieren
                        
                        # Inkrementiere completed_offers_count für alle betroffenen Dienstleister
                        try:
                            from .milestone_completion_service import MilestoneCompletionService
                            await MilestoneCompletionService.increment_completed_offers_count(db, milestone.id)
                            print(f"[SUCCESS] completed_offers_count für betroffene Dienstleister von Milestone {milestone.id} inkrementiert")
                        except Exception as e:
                            print(f"[WARNING] Fehler beim Inkrementieren der completed_offers_count: {e}")
                            # Fehler nicht kritisch, da Hauptfunktion (Abnahme) bereits erfolgreich
                        
                        # Vergebe Credits an Bauträger für Projekt-Abschluss
                        try:
                            from .credit_service import CreditService
                            from ..models.credit_event import CreditEventType
                            
                            # Hole Projekt um Owner (Bauträger) zu ermitteln
                            project_result = await db.execute(
                                select(Project).where(Project.id == milestone.project_id)
                            )
                            project = project_result.scalar_one_or_none()
                            
                            if project:
                                # Hole Owner-ID
                                owner_id = project.owner.id if hasattr(project.owner, 'id') else project.owner_id
                                
                                # Vergebe Credits für Projekt-Abschluss
                                await CreditService.add_credits_for_activity(
                                    db=db,
                                    user_id=owner_id,
                                    event_type=CreditEventType.PROJECT_COMPLETED,
                                    description=f"Projekt abgeschlossen: {milestone.title}",
                                    related_entity_type="milestone",
                                    related_entity_id=milestone.id
                                )
                                print(f"[SUCCESS] Credits für Projekt-Abschluss an Bauträger {owner_id} vergeben")
                        except Exception as e:
                            print(f"[WARNING] Fehler bei Credit-Vergabe für Projekt-Abschluss: {e}")
                            # Fehler bei Credit-Vergabe sollte nicht die Abnahme blockieren
                    else:
                        milestone.completion_status = 'completed_with_defects'
                        print(f"[WARNING] Milestone {milestone.title} als 'abgenommen unter Vorbehalt' markiert")
                        
                        # Sende Benachrichtigung an den Dienstleister über die Abnahme unter Vorbehalt
                        try:
                            from .notification_service import NotificationService
                            
                            # Ermittle Service Provider ID
                            service_provider_id = None
                            if acceptance.service_provider_id:
                                service_provider_id = acceptance.service_provider_id
                            elif milestone.accepted_by:
                                service_provider_id = milestone.accepted_by
                            
                            if service_provider_id and service_provider_id != completed_by_user_id:
                                notification = await NotificationService.create_acceptance_with_defects_notification(
                                    db=db,
                                    milestone_id=milestone.id,
                                    service_provider_id=service_provider_id,
                                    bautraeger_id=completed_by_user_id
                                )
                                print(f"[SUCCESS] Benachrichtigung für Abnahme unter Vorbehalt an Service Provider {service_provider_id} gesendet")
                            else:
                                print(f"[WARNING] Kein Service Provider für Benachrichtigung gefunden (Service Provider ID: {service_provider_id}, Bauträger ID: {completed_by_user_id})")
                                
                        except Exception as e:
                            print(f"[ERROR] Fehler beim Senden der Abnahme-unter-Vorbehalt-Benachrichtigung: {e}")
                            # Fehler bei Benachrichtigung sollte nicht die Abnahme blockieren
            
            # Commit alle Änderungen in einem Rutsch
            await db.commit()
            
            # Automatische Task-Erstellung in separater Session
            print("🤖 Starte automatische Task-Erstellung...")
            task_result = await process_acceptance_completion(
                db=db,
                acceptance=acceptance,
                created_by_user_id=completed_by_user_id
            )
            
            print(f"[SUCCESS] Abnahme abgeschlossen: {task_result['defect_tasks_created']} Mangel-Tasks (Dienstleister), {task_result.get('monitoring_tasks_created', 0)} Überwachungs-Tasks (Bauträger), {'1' if task_result['review_task_created'] else '0'} Wiedervorlage-Task erstellt")
            
            return acceptance
            
        except Exception as e:
            await db.rollback()
            print(f"[ERROR] Fehler beim Abschließen der Abnahme: {e}")
            raise

    @staticmethod
    async def store_in_dms(
        db: AsyncSession,
        acceptance: Acceptance,
        pdf_path: str
    ) -> None:
        """Speichere Abnahmeprotokoll im DMS"""
        try:
            import os
            
            print(f"📁 Speichere Abnahmeprotokoll im DMS: {pdf_path}")
            
            # Erstelle Dokument-Eintrag im DMS
            document_title = f"Abnahmeprotokoll_{acceptance.milestone.title if acceptance.milestone else 'Gewerk'}_{acceptance.id}"
            
            # Lese PDF-Datei
            if os.path.exists(pdf_path):
                print(f"[SUCCESS] Abnahmeprotokoll würde im DMS gespeichert: {document_title}")
                # TODO: Vollständige DMS-Integration implementieren
                # Hier würde das Dokument in das DMS-System eingetragen werden
                
            else:
                print(f"[WARNING] PDF-Datei nicht gefunden: {pdf_path}")
                
        except Exception as e:
            print(f"[ERROR] Fehler bei DMS-Integration: {e}")
            # Fehler nicht weiterwerfen, da Abnahme bereits erfolgreich

    # [DEBUG] Mängel-Management Methoden
    
    @staticmethod
    async def get_milestone_defects(
        db: AsyncSession, 
        milestone_id: int, 
        user_id: int
    ) -> List[Dict[str, Any]]:
        """Lade alle Mängel für ein Gewerk"""
        try:
            print(f"[DEBUG] Lade Mängel für Milestone {milestone_id}")
            
            # Lade Mängel aus der Acceptance mit dem entsprechenden Milestone
            result = await db.execute(
                select(AcceptanceDefect)
                .join(Acceptance, AcceptanceDefect.acceptance_id == Acceptance.id)
                .where(Acceptance.milestone_id == milestone_id)
                .options(joinedload(AcceptanceDefect.acceptance))
                .order_by(AcceptanceDefect.created_at.desc())
            )
            
            defects = result.scalars().all()
            
            # Konvertiere zu Dictionary-Format
            defects_data = []
            for defect in defects:
                defects_data.append({
                    "id": defect.id,
                    "description": defect.description,
                    "category": defect.category,
                    "severity": defect.severity.value if defect.severity else "medium",
                    "created_at": defect.created_at.isoformat() if defect.created_at else None,
                    "resolved": defect.resolved or False,
                    "resolved_at": defect.resolved_at.isoformat() if defect.resolved_at else None,
                    "resolution_notes": defect.resolution_notes,
                    "acceptance_id": defect.acceptance_id
                })
            
            print(f"[SUCCESS] {len(defects_data)} Mängel für Milestone {milestone_id} geladen")
            return defects_data
            
        except Exception as e:
            print(f"[ERROR] Fehler beim Laden der Mängel: {e}")
            raise e

    @staticmethod
    async def resolve_defect(
        db: AsyncSession,
        milestone_id: int,
        defect_id: int,
        resolution_data: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """Markiere einen Mangel als behoben oder unbehoben"""
        try:
            print(f"[DEBUG] Markiere Mangel {defect_id} als {'behoben' if resolution_data.get('resolved') else 'unbehoben'}")
            
            # Lade den Mangel
            result = await db.execute(
                select(AcceptanceDefect)
                .join(Acceptance, AcceptanceDefect.acceptance_id == Acceptance.id)
                .where(
                    and_(
                        AcceptanceDefect.id == defect_id,
                        Acceptance.milestone_id == milestone_id
                    )
                )
            )
            
            defect = result.scalar_one_or_none()
            if not defect:
                raise ValueError(f"Mangel {defect_id} für Milestone {milestone_id} nicht gefunden")
            
            # Aktualisiere den Status
            defect.resolved = resolution_data.get('resolved', False)
            defect.resolution_notes = resolution_data.get('resolution_notes', '')
            
            if defect.resolved:
                defect.resolved_at = datetime.utcnow()
            else:
                defect.resolved_at = None
            
            await db.commit()
            
            print(f"[SUCCESS] Mangel {defect_id} erfolgreich aktualisiert")
            
            return {
                "id": defect.id,
                "description": defect.description,
                "resolved": defect.resolved,
                "resolved_at": defect.resolved_at.isoformat() if defect.resolved_at else None,
                "resolution_notes": defect.resolution_notes
            }
            
        except Exception as e:
            print(f"[ERROR] Fehler beim Aktualisieren des Mangels: {e}")
            await db.rollback()
            raise e

    @staticmethod
    async def submit_defect_resolution(
        db: AsyncSession,
        milestone_id: int,
        resolution_data: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """Melde alle Mängel als behoben und bereit für finale Abnahme"""
        try:
            print(f"[INFO] Melde Mängelbehebung für Milestone {milestone_id}")
            
            # Prüfe ob alle Mängel behoben sind
            result = await db.execute(
                select(func.count(AcceptanceDefect.id), func.count(AcceptanceDefect.id).filter(AcceptanceDefect.resolved == True))
                .join(Acceptance, AcceptanceDefect.acceptance_id == Acceptance.id)
                .where(Acceptance.milestone_id == milestone_id)
            )
            
            total_defects, resolved_defects = result.first()
            
            if total_defects == 0:
                raise ValueError("Keine Mängel für dieses Gewerk gefunden")
            
            if resolved_defects != total_defects:
                raise ValueError(f"Nicht alle Mängel behoben: {resolved_defects}/{total_defects}")
            
            # Aktualisiere Milestone Status für finale Abnahme-Bereitschaft
            milestone_result = await db.execute(
                select(Milestone).where(Milestone.id == milestone_id)
            )
            milestone = milestone_result.scalar_one_or_none()
            
            if milestone:
                # Setze einen Flag oder Status für "bereit für finale Abnahme"
                milestone.defects_resolved = True
                milestone.defects_resolved_at = datetime.utcnow()
                
                # Aktualisiere completion_status auf 'defects_resolved'
                milestone.completion_status = 'defects_resolved'
                
                # Optional: Erstelle eine Benachrichtigung für den Bauträger
                # TODO: Implementiere Benachrichtigungssystem
                
                await db.commit()
                
                print(f"[SUCCESS] Milestone {milestone_id} als bereit für finale Abnahme markiert (completion_status: defects_resolved)")
                
                return {
                    "milestone_id": milestone_id,
                    "total_defects": total_defects,
                    "resolved_defects": resolved_defects,
                    "ready_for_final_acceptance": True,
                    "completion_status": "defects_resolved",
                    "message": resolution_data.get('message', 'Alle Mängel behoben')
                }
            else:
                raise ValueError(f"Milestone {milestone_id} nicht gefunden")
                
        except Exception as e:
            print(f"[ERROR] Fehler beim Melden der Mängelbehebung: {e}")
            await db.rollback()
            raise e

    @staticmethod
    async def get_defect_resolution_status(
        db: AsyncSession,
        milestone_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """Prüfe den Status der Mängelbehebung für ein Gewerk"""
        try:
            print(f"[DEBUG] Prüfe Mängelbehebungsstatus für Milestone {milestone_id}")
            
            # Zähle Mängel und behobene Mängel
            result = await db.execute(
                select(
                    func.count(AcceptanceDefect.id).label('total_defects'),
                    func.count(AcceptanceDefect.id).filter(AcceptanceDefect.resolved == True).label('resolved_defects')
                )
                .join(Acceptance, AcceptanceDefect.acceptance_id == Acceptance.id)
                .where(Acceptance.milestone_id == milestone_id)
            )
            
            row = result.first()
            total_defects = row.total_defects or 0
            resolved_defects = row.resolved_defects or 0
            
            all_resolved = total_defects > 0 and resolved_defects == total_defects
            
            # Prüfe Milestone-Status
            milestone_result = await db.execute(
                select(Milestone.defects_resolved, Milestone.defects_resolved_at)
                .where(Milestone.id == milestone_id)
            )
            milestone_data = milestone_result.first()
            
            status = {
                "milestone_id": milestone_id,
                "total_defects": total_defects,
                "resolved_defects": resolved_defects,
                "all_resolved": all_resolved,
                "ready_for_final_acceptance": milestone_data.defects_resolved if milestone_data else False,
                "defects_resolved_at": milestone_data.defects_resolved_at.isoformat() if milestone_data and milestone_data.defects_resolved_at else None
            }
            
            print(f"[SUCCESS] Mängelbehebungsstatus: {status}")
            return status
            
        except Exception as e:
            print(f"[ERROR] Fehler beim Prüfen des Mängelbehebungsstatus: {e}")
            raise e