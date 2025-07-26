"""
Inspection Service für BuildWise
Handhabt den gesamten Besichtigungsprozess
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from ..models.inspection import Inspection, InspectionStatus, InspectionInvitation, InspectionInvitationStatus, QuoteRevision
from ..models.milestone import Milestone
from ..models.quote import Quote
from ..models.user import User
from ..models.project import Project

logger = logging.getLogger(__name__)


class InspectionService:
    """Service für Besichtigungsprozesse"""
    
    async def create_inspection(
        self,
        db: AsyncSession,
        milestone_id: int,
        created_by: int,
        scheduled_date: date,
        title: str,
        description: Optional[str] = None,
        scheduled_time_start: Optional[str] = None,
        scheduled_time_end: Optional[str] = None,
        duration_minutes: int = 120,
        location_address: Optional[str] = None,
        location_notes: Optional[str] = None,
        contact_person: Optional[str] = None,
        contact_phone: Optional[str] = None,
        preparation_notes: Optional[str] = None
    ) -> Optional[Inspection]:
        """
        Erstellt eine neue Besichtigung für ein Gewerk
        
        Args:
            db: Datenbank-Session
            milestone_id: ID des Gewerks
            created_by: ID des Bauträgers
            scheduled_date: Geplantes Datum
            title: Titel der Besichtigung
            description: Beschreibung
            scheduled_time_start: Startzeit (z.B. "14:00")
            scheduled_time_end: Endzeit (z.B. "16:00")
            duration_minutes: Dauer in Minuten
            location_address: Spezifische Adresse
            location_notes: Zusätzliche Ortsangaben
            contact_person: Ansprechpartner
            contact_phone: Telefonnummer
            preparation_notes: Vorbereitungshinweise
            
        Returns:
            Erstellte Besichtigung oder None bei Fehler
        """
        try:
            # Milestone und Projekt laden
            milestone_result = await db.execute(
                select(Milestone).options(selectinload(Milestone.project))
                .where(Milestone.id == milestone_id)
            )
            milestone = milestone_result.scalar_one_or_none()
            
            if not milestone:
                logger.error(f"Milestone {milestone_id} nicht gefunden")
                return None
            
            # Besichtigung erstellen
            inspection = Inspection(
                milestone_id=milestone_id,
                project_id=milestone.project_id,
                created_by=created_by,
                title=title,
                description=description,
                scheduled_date=scheduled_date,
                scheduled_time_start=scheduled_time_start,
                scheduled_time_end=scheduled_time_end,
                duration_minutes=duration_minutes,
                location_address=location_address,
                location_notes=location_notes,
                contact_person=contact_person,
                contact_phone=contact_phone,
                preparation_notes=preparation_notes,
                status=InspectionStatus.PLANNED
            )
            
            db.add(inspection)
            await db.commit()
            await db.refresh(inspection)
            
            logger.info(f"Besichtigung {inspection.id} für Milestone {milestone_id} erstellt")
            return inspection
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Besichtigung: {str(e)}")
            await db.rollback()
            return None
    
    async def invite_service_providers(
        self,
        db: AsyncSession,
        inspection_id: int,
        quote_ids: List[int]
    ) -> List[InspectionInvitation]:
        """
        Lädt Dienstleister zur Besichtigung ein basierend auf ihren Angeboten
        
        Args:
            db: Datenbank-Session
            inspection_id: ID der Besichtigung
            quote_ids: Liste der Quote-IDs (Angebote die eingeladen werden)
            
        Returns:
            Liste der erstellten Einladungen
        """
        try:
            invitations = []
            
            # Quotes mit Dienstleister-Informationen laden
            quotes_result = await db.execute(
                select(Quote).options(selectinload(Quote.service_provider))
                .where(Quote.id.in_(quote_ids))
            )
            quotes = quotes_result.scalars().all()
            
            for quote in quotes:
                # Prüfen ob bereits eine Einladung existiert
                existing_result = await db.execute(
                    select(InspectionInvitation).where(
                        and_(
                            InspectionInvitation.inspection_id == inspection_id,
                            InspectionInvitation.service_provider_id == quote.service_provider_id
                        )
                    )
                )
                existing = existing_result.scalar_one_or_none()
                
                if existing:
                    logger.warning(f"Einladung für Dienstleister {quote.service_provider_id} existiert bereits")
                    continue
                
                # Einladung erstellen
                invitation = InspectionInvitation(
                    inspection_id=inspection_id,
                    service_provider_id=quote.service_provider_id,
                    quote_id=quote.id,
                    status=InspectionInvitationStatus.SENT
                )
                
                db.add(invitation)
                invitations.append(invitation)
            
            await db.commit()
            
            # Besichtigungsstatus aktualisieren
            await self.update_inspection_status(db, inspection_id, InspectionStatus.INVITED)
            
            logger.info(f"{len(invitations)} Einladungen für Besichtigung {inspection_id} erstellt")
            return invitations
            
        except Exception as e:
            logger.error(f"Fehler beim Einladen der Dienstleister: {str(e)}")
            await db.rollback()
            return []
    
    async def respond_to_invitation(
        self,
        db: AsyncSession,
        invitation_id: int,
        service_provider_id: int,
        status: InspectionInvitationStatus,
        response_message: Optional[str] = None,
        alternative_dates: Optional[str] = None
    ) -> bool:
        """
        Dienstleister antwortet auf Besichtigungseinladung
        
        Args:
            db: Datenbank-Session
            invitation_id: ID der Einladung
            service_provider_id: ID des Dienstleisters
            status: Antwort (CONFIRMED, DECLINED)
            response_message: Nachricht
            alternative_dates: Alternative Termine (JSON)
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Einladung laden und Berechtigung prüfen
            invitation_result = await db.execute(
                select(InspectionInvitation).where(
                    and_(
                        InspectionInvitation.id == invitation_id,
                        InspectionInvitation.service_provider_id == service_provider_id
                    )
                )
            )
            invitation = invitation_result.scalar_one_or_none()
            
            if not invitation:
                logger.error(f"Einladung {invitation_id} nicht gefunden oder keine Berechtigung")
                return False
            
            # Antwort speichern
            invitation.status = status
            invitation.response_message = response_message
            invitation.alternative_dates = alternative_dates
            invitation.responded_at = datetime.utcnow()
            
            await db.commit()
            
            logger.info(f"Antwort auf Einladung {invitation_id}: {status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Antworten auf Einladung: {str(e)}")
            await db.rollback()
            return False
    
    async def create_quote_revision(
        self,
        db: AsyncSession,
        original_quote_id: int,
        inspection_id: int,
        service_provider_id: int,
        title: str,
        description: Optional[str],
        revision_reason: Optional[str],
        total_amount: float,
        currency: str = "EUR",
        valid_until: Optional[date] = None,
        labor_cost: Optional[float] = None,
        material_cost: Optional[float] = None,
        overhead_cost: Optional[float] = None,
        estimated_duration: Optional[int] = None,
        start_date: Optional[date] = None,
        completion_date: Optional[date] = None,
        pdf_upload_path: Optional[str] = None,
        additional_documents: Optional[str] = None
    ) -> Optional[QuoteRevision]:
        """
        Erstellt ein überarbeitetes Angebot nach Besichtigung
        
        Args:
            db: Datenbank-Session
            original_quote_id: ID des ursprünglichen Angebots
            inspection_id: ID der Besichtigung
            service_provider_id: ID des Dienstleisters
            title: Titel des revidierten Angebots
            description: Beschreibung
            revision_reason: Grund für die Überarbeitung
            total_amount: Neuer Gesamtbetrag
            currency: Währung
            valid_until: Gültig bis
            labor_cost: Arbeitskosten
            material_cost: Materialkosten
            overhead_cost: Gemeinkosten
            estimated_duration: Geschätzte Dauer
            start_date: Startdatum
            completion_date: Fertigstellungsdatum
            pdf_upload_path: Pfad zum PDF
            additional_documents: Zusätzliche Dokumente (JSON)
            
        Returns:
            Erstellte Quote-Revision oder None bei Fehler
        """
        try:
            # Original-Quote laden für Vergleich
            original_quote_result = await db.execute(
                select(Quote).where(Quote.id == original_quote_id)
            )
            original_quote = original_quote_result.scalar_one_or_none()
            
            if not original_quote:
                logger.error(f"Original-Quote {original_quote_id} nicht gefunden")
                return None
            
            # Differenz berechnen
            amount_difference = total_amount - original_quote.total_amount
            amount_difference_percentage = (amount_difference / original_quote.total_amount) * 100 if original_quote.total_amount > 0 else 0
            
            # Quote-Revision erstellen
            revision = QuoteRevision(
                original_quote_id=original_quote_id,
                inspection_id=inspection_id,
                service_provider_id=service_provider_id,
                title=title,
                description=description,
                revision_reason=revision_reason,
                total_amount=total_amount,
                currency=currency,
                valid_until=valid_until,
                labor_cost=labor_cost,
                material_cost=material_cost,
                overhead_cost=overhead_cost,
                amount_difference=amount_difference,
                amount_difference_percentage=amount_difference_percentage,
                estimated_duration=estimated_duration,
                start_date=start_date,
                completion_date=completion_date,
                pdf_upload_path=pdf_upload_path,
                additional_documents=additional_documents,
                status="submitted"
            )
            
            db.add(revision)
            await db.commit()
            await db.refresh(revision)
            
            logger.info(f"Quote-Revision {revision.id} für Original-Quote {original_quote_id} erstellt")
            return revision
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Quote-Revision: {str(e)}")
            await db.rollback()
            return None
    
    async def confirm_quote_revision(
        self,
        db: AsyncSession,
        revision_id: int,
        confirmed_by: int
    ) -> bool:
        """
        Bauträger bestätigt eine Quote-Revision
        
        Args:
            db: Datenbank-Session
            revision_id: ID der Quote-Revision
            confirmed_by: ID des Bauträgers
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Revision laden
            revision_result = await db.execute(
                select(QuoteRevision).where(QuoteRevision.id == revision_id)
            )
            revision = revision_result.scalar_one_or_none()
            
            if not revision:
                logger.error(f"Quote-Revision {revision_id} nicht gefunden")
                return False
            
            # Bestätigung speichern
            revision.confirmed_by_client = True
            revision.confirmed_at = datetime.utcnow()
            revision.status = "accepted"
            
            await db.commit()
            
            # TODO: Hier würde die Provision (BuildWise Fee) erstellt werden
            # await self.create_buildwise_fee_for_revision(db, revision)
            
            logger.info(f"Quote-Revision {revision_id} bestätigt")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Bestätigen der Quote-Revision: {str(e)}")
            await db.rollback()
            return False
    
    async def get_inspections_for_milestone(
        self,
        db: AsyncSession,
        milestone_id: int
    ) -> List[Inspection]:
        """
        Lädt alle Besichtigungen für ein Gewerk
        
        Args:
            db: Datenbank-Session
            milestone_id: ID des Gewerks
            
        Returns:
            Liste der Besichtigungen
        """
        try:
            result = await db.execute(
                select(Inspection)
                .options(selectinload(Inspection.invitations))
                .where(Inspection.milestone_id == milestone_id)
                .order_by(Inspection.scheduled_date.desc())
            )
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Besichtigungen: {str(e)}")
            return []
    
    async def get_invitations_for_service_provider(
        self,
        db: AsyncSession,
        service_provider_id: int,
        status: Optional[InspectionInvitationStatus] = None
    ) -> List[InspectionInvitation]:
        """
        Lädt Besichtigungseinladungen für einen Dienstleister
        
        Args:
            db: Datenbank-Session
            service_provider_id: ID des Dienstleisters
            status: Optional filter nach Status
            
        Returns:
            Liste der Einladungen
        """
        try:
            query = select(InspectionInvitation).options(
                selectinload(InspectionInvitation.inspection),
                selectinload(InspectionInvitation.quote)
            ).where(InspectionInvitation.service_provider_id == service_provider_id)
            
            if status:
                query = query.where(InspectionInvitation.status == status)
            
            result = await db.execute(query.order_by(InspectionInvitation.created_at.desc()))
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Einladungen: {str(e)}")
            return []
    
    async def get_quote_revisions_for_inspection(
        self,
        db: AsyncSession,
        inspection_id: int
    ) -> List[QuoteRevision]:
        """
        Lädt alle Quote-Revisionen für eine Besichtigung
        
        Args:
            db: Datenbank-Session
            inspection_id: ID der Besichtigung
            
        Returns:
            Liste der Quote-Revisionen
        """
        try:
            result = await db.execute(
                select(QuoteRevision)
                .options(
                    selectinload(QuoteRevision.original_quote),
                    selectinload(QuoteRevision.service_provider)
                )
                .where(QuoteRevision.inspection_id == inspection_id)
                .order_by(QuoteRevision.created_at.desc())
            )
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Quote-Revisionen: {str(e)}")
            return []
    
    async def update_inspection_status(
        self,
        db: AsyncSession,
        inspection_id: int,
        status: InspectionStatus
    ) -> bool:
        """
        Aktualisiert den Status einer Besichtigung
        
        Args:
            db: Datenbank-Session
            inspection_id: ID der Besichtigung
            status: Neuer Status
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            result = await db.execute(
                select(Inspection).where(Inspection.id == inspection_id)
            )
            inspection = result.scalar_one_or_none()
            
            if not inspection:
                return False
            
            inspection.status = status
            if status == InspectionStatus.COMPLETED:
                inspection.completed_at = datetime.utcnow()
            
            await db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren des Besichtigungsstatus: {str(e)}")
            await db.rollback()
            return False

    async def get_inspections_for_user(
        self,
        db: AsyncSession,
        user_id: int
    ) -> List[Inspection]:
        """
        Lädt alle Besichtigungen für einen Benutzer (Bauträger)
        
        Args:
            db: Datenbank-Session
            user_id: ID des Benutzers
            
        Returns:
            Liste der Besichtigungen
        """
        try:
            result = await db.execute(
                select(Inspection)
                .options(
                    selectinload(Inspection.invitations).selectinload(InspectionInvitation.service_provider),
                    selectinload(Inspection.milestone),
                    selectinload(Inspection.project)
                )
                .where(Inspection.created_by == user_id)
                .order_by(Inspection.scheduled_date.desc())
            )
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Benutzer-Besichtigungen: {str(e)}")
            return []

    async def reject_quote_revision(
        self,
        db: AsyncSession,
        revision_id: int,
        rejected_by: int,
        rejection_reason: Optional[str] = None
    ) -> bool:
        """
        Bauträger lehnt eine Quote-Revision ab
        
        Args:
            db: Datenbank-Session
            revision_id: ID der Quote-Revision
            rejected_by: ID des Bauträgers
            rejection_reason: Grund der Ablehnung
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Revision laden
            revision_result = await db.execute(
                select(QuoteRevision).where(QuoteRevision.id == revision_id)
            )
            revision = revision_result.scalar_one_or_none()
            
            if not revision:
                logger.error(f"Quote-Revision {revision_id} nicht gefunden")
                return False
            
            # Ablehnung speichern
            revision.status = "rejected"
            revision.rejection_reason = rejection_reason
            revision.rejected_at = datetime.utcnow()
            revision.rejected_by = rejected_by
            
            await db.commit()
            
            logger.info(f"Quote-Revision {revision_id} abgelehnt")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Ablehnen der Quote-Revision: {str(e)}")
            await db.rollback()
            return False

    async def complete_inspection(
        self,
        db: AsyncSession,
        inspection_id: int,
        completion_notes: Optional[str] = None
    ) -> bool:
        """
        Markiert eine Besichtigung als abgeschlossen
        
        Args:
            db: Datenbank-Session
            inspection_id: ID der Besichtigung
            completion_notes: Abschlussnotizen
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            result = await db.execute(
                select(Inspection).where(Inspection.id == inspection_id)
            )
            inspection = result.scalar_one_or_none()
            
            if not inspection:
                return False
            
            inspection.status = InspectionStatus.COMPLETED
            inspection.completed_at = datetime.utcnow()
            inspection.completion_notes = completion_notes
            
            await db.commit()
            
            logger.info(f"Besichtigung {inspection_id} abgeschlossen")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Abschließen der Besichtigung: {str(e)}")
            await db.rollback()
            return False

    async def cancel_inspection(
        self,
        db: AsyncSession,
        inspection_id: int,
        cancellation_reason: Optional[str] = None
    ) -> bool:
        """
        Bricht eine Besichtigung ab
        
        Args:
            db: Datenbank-Session
            inspection_id: ID der Besichtigung
            cancellation_reason: Grund der Absage
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            result = await db.execute(
                select(Inspection).where(Inspection.id == inspection_id)
            )
            inspection = result.scalar_one_or_none()
            
            if not inspection:
                return False
            
            inspection.status = InspectionStatus.CANCELLED
            inspection.cancellation_reason = cancellation_reason
            inspection.cancelled_at = datetime.utcnow()
            
            await db.commit()
            
            logger.info(f"Besichtigung {inspection_id} abgebrochen")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Abbrechen der Besichtigung: {str(e)}")
            await db.rollback()
            return False

    async def get_inspection_required_milestones(
        self,
        db: AsyncSession,
        user_id: int
    ) -> List[dict]:
        """
        Lädt alle Gewerke mit requires_inspection = True für einen Bauträger
        
        Args:
            db: Datenbank-Session
            user_id: ID des Bauträgers
            
        Returns:
            Liste der besichtigungspflichtigen Gewerke
        """
        try:
            # Lade Milestones mit requires_inspection = True für Projekte des Benutzers
            result = await db.execute(
                select(Milestone)
                .options(selectinload(Milestone.project))
                .join(Project)
                .where(
                    and_(
                        Milestone.requires_inspection == True,
                        Project.created_by == user_id
                    )
                )
                .order_by(Milestone.created_at.desc())
            )
            milestones = list(result.scalars().all())
            
            # Konvertiere zu Dict-Format für Frontend
            milestone_dicts = []
            for milestone in milestones:
                milestone_dict = {
                    "id": milestone.id,
                    "title": milestone.title,
                    "description": milestone.description,
                    "category": milestone.category,
                    "budget": milestone.budget,
                    "requires_inspection": milestone.requires_inspection,
                    "status": milestone.status,
                    "start_date": milestone.start_date.isoformat() if milestone.start_date else None,
                    "project_id": milestone.project_id,
                    "project_name": milestone.project.name if milestone.project else None
                }
                milestone_dicts.append(milestone_dict)
            
            return milestone_dicts
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der besichtigungspflichtigen Gewerke: {str(e)}")
            return []


# Singleton-Instanz
inspection_service = InspectionService() 