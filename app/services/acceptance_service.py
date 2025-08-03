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
            print(f"🔧 Erstelle Abnahme für Milestone {acceptance_data.milestone_id}")
            
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
            
            print(f"✅ Abnahme {acceptance.id} erstellt")
            return acceptance
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Fehler beim Erstellen der Abnahme: {e}")
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
            print(f"📅 Erstelle Abnahme-Termin für Milestone {milestone_id}")
            
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
            
            print(f"✅ Abnahme-Termin {appointment.id} erstellt")
            return appointment
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Fehler beim Erstellen des Abnahme-Termins: {e}")
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
            print(f"📝 Antwort auf Abnahme-Termin {appointment_id}: {'Akzeptiert' if accepted else 'Abgelehnt'}")
            
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
            
            print(f"✅ Antwort auf Abnahme-Termin gespeichert")
            return appointment
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Fehler bei Antwort auf Abnahme-Termin: {e}")
            raise


    @staticmethod
    async def start_acceptance(
        db: AsyncSession,
        acceptance_id: int,
        user_id: int
    ) -> Acceptance:
        """Starte die Abnahme"""
        try:
            print(f"🚀 Starte Abnahme {acceptance_id}")
            
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
            
            print(f"✅ Abnahme {acceptance_id} gestartet")
            return acceptance
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Fehler beim Starten der Abnahme: {e}")
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
            print(f"❌ Fehler beim Laden der Abnahme: {e}")
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
            print(f"❌ Fehler beim Laden der Abnahmen: {e}")
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
            print(f"❌ Fehler bei Abnahme-Zusammenfassung: {e}")
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
            print(f"🏁 Schließe Abnahme {acceptance_id} ab...")
            
            # Hole Abnahme
            result = await db.execute(
                select(Acceptance)
                .options(selectinload(Acceptance.defects))
                .where(Acceptance.id == acceptance_id)
            )
            acceptance = result.scalars().first()
            
            if not acceptance:
                raise ValueError(f"Abnahme {acceptance_id} nicht gefunden")
            
            # Aktualisiere Abnahme-Status
            acceptance.status = AcceptanceStatus.COMPLETED
            acceptance.completed_at = datetime.now()
            acceptance.accepted = completion_data.get('accepted', False)
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
                acceptance.defects.append(defect)
            
            await db.commit()
            await db.refresh(acceptance)
            
            # Automatische Task-Erstellung
            print("🤖 Starte automatische Task-Erstellung...")
            task_result = await process_acceptance_completion(
                db=db,
                acceptance=acceptance,
                created_by_user_id=completed_by_user_id
            )
            
            print(f"✅ Abnahme abgeschlossen: {task_result['defect_tasks_created']} Mangel-Tasks, {'1' if task_result['review_task_created'] else '0'} Wiedervorlage-Task erstellt")
            
            # Aktualisiere Milestone-Status
            if acceptance.milestone_id:
                milestone_result = await db.execute(select(Milestone).where(Milestone.id == acceptance.milestone_id))
                milestone = milestone_result.scalars().first()
                
                if milestone:
                    if acceptance.accepted:
                        milestone.completion_status = 'completed'
                        milestone.status = 'completed'
                        milestone.completed_at = datetime.now()
                        print(f"✅ Milestone {milestone.title} als abgenommen markiert")
                    else:
                        milestone.completion_status = 'completed_with_defects'
                        print(f"⚠️ Milestone {milestone.title} als 'abgenommen unter Vorbehalt' markiert")
                    
                    await db.commit()
            
            return acceptance
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Fehler beim Abschließen der Abnahme: {e}")
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
                print(f"✅ Abnahmeprotokoll würde im DMS gespeichert: {document_title}")
                # TODO: Vollständige DMS-Integration implementieren
                # Hier würde das Dokument in das DMS-System eingetragen werden
                
            else:
                print(f"⚠️ PDF-Datei nicht gefunden: {pdf_path}")
                
        except Exception as e:
            print(f"❌ Fehler bei DMS-Integration: {e}")
            # Fehler nicht weiterwerfen, da Abnahme bereits erfolgreich