from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models.user import User
from ..models.inspection import QuoteRevision
from ..schemas.inspection import (
    InspectionCreate, InspectionRead, InspectionUpdate, InspectionSummary,
    InspectionInvitationUpdate, InspectionInvitationRead,
    QuoteRevisionCreate, QuoteRevisionRead, QuoteRevisionUpdate
)
from ..services.inspection_service import inspection_service
from ..services.credit_service import CreditService

router = APIRouter(prefix="/inspections", tags=["inspections"])


@router.post("/", response_model=InspectionRead, status_code=status.HTTP_201_CREATED)
async def create_inspection(
    inspection_data: InspectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Erstellt eine neue Besichtigung"""
    user_id = getattr(current_user, 'id', 0)
    
    try:
        inspection = await inspection_service.create_inspection(
            db=db,
            milestone_id=inspection_data.milestone_id,
            created_by=user_id,
            scheduled_date=inspection_data.scheduled_date,
            title=inspection_data.title,
            description=inspection_data.description,
            scheduled_time_start=inspection_data.scheduled_time_start,
            scheduled_time_end=inspection_data.scheduled_time_end,
            duration_minutes=inspection_data.duration_minutes or 120,
            location_address=inspection_data.location_address,
            location_notes=inspection_data.location_notes,
            contact_person=inspection_data.contact_person,
            contact_phone=inspection_data.contact_phone,
            preparation_notes=inspection_data.preparation_notes
        )
        
        if not inspection:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Besichtigung konnte nicht erstellt werden"
            )
            
        return inspection
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fehler beim Erstellen der Besichtigung: {str(e)}"
        )


@router.post("/{inspection_id}/invitations", status_code=status.HTTP_201_CREATED)
async def invite_service_providers(
    inspection_id: int,
    quote_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lädt Dienstleister zur Besichtigung ein basierend auf ihren Angeboten"""
    try:
        invitations = await inspection_service.invite_service_providers(
            db=db,
            inspection_id=inspection_id,
            quote_ids=quote_ids
        )
        
        return {
            "message": f"{len(invitations)} Einladungen versendet",
            "invitations_count": len(invitations)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fehler beim Versenden der Einladungen: {str(e)}"
        )


@router.get("/", response_model=List[InspectionRead])
async def get_inspections(
    milestone_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lädt Besichtigungen für den aktuellen Benutzer"""
    try:
        if milestone_id:
            inspections = await inspection_service.get_inspections_for_milestone(
                db=db,
                milestone_id=milestone_id
            )
        else:
            # Alle Besichtigungen für den Benutzer (als Bauträger)
            inspections = await inspection_service.get_inspections_for_user(
                db=db,
                user_id=current_user.id
            )
        
        return inspections
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fehler beim Laden der Besichtigungen: {str(e)}"
        )


@router.get("/invitations", response_model=List[InspectionInvitationRead])
async def get_my_invitations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lädt Besichtigungseinladungen für den aktuellen Dienstleister"""
    try:
        invitations = await inspection_service.get_invitations_for_service_provider(
            db=db,
            service_provider_id=current_user.id
        )
        return invitations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fehler beim Laden der Einladungen: {str(e)}"
        )


@router.put("/invitations/{invitation_id}/respond")
async def respond_to_invitation(
    invitation_id: int,
    response_data: InspectionInvitationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Dienstleister antwortet auf Besichtigungseinladung"""
    try:
        success = await inspection_service.respond_to_invitation(
            db=db,
            invitation_id=invitation_id,
            service_provider_id=current_user.id,
            status=response_data.status,
            response_message=response_data.response_message,
            alternative_dates=response_data.alternative_dates
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Antwort konnte nicht gespeichert werden"
            )
            
        return {"message": "Antwort erfolgreich gespeichert"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fehler beim Antworten: {str(e)}"
        )


@router.post("/{inspection_id}/quote-revisions", response_model=QuoteRevisionRead, status_code=status.HTTP_201_CREATED)
async def create_quote_revision(
    inspection_id: int,
    revision_data: QuoteRevisionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Erstellt ein überarbeitetes Angebot nach Besichtigung"""
    try:
        revision = await inspection_service.create_quote_revision(
            db=db,
            original_quote_id=revision_data.original_quote_id,
            inspection_id=inspection_id,
            service_provider_id=current_user.id,
            title=revision_data.title,
            description=revision_data.description,
            revision_reason=revision_data.revision_reason,
            total_amount=revision_data.total_amount,
            currency=revision_data.currency or "EUR",
            valid_until=revision_data.valid_until,
            labor_cost=revision_data.labor_cost,
            material_cost=revision_data.material_cost,
            overhead_cost=revision_data.overhead_cost,
            estimated_duration=revision_data.estimated_duration,
            start_date=revision_data.start_date,
            completion_date=revision_data.completion_date,
            pdf_upload_path=revision_data.pdf_upload_path,
            additional_documents=revision_data.additional_documents
        )
        
        if not revision:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quote-Revision konnte nicht erstellt werden"
            )
            
        return revision
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fehler beim Erstellen der Quote-Revision: {str(e)}"
        )


@router.get("/{inspection_id}/quote-revisions", response_model=List[QuoteRevisionRead])
async def get_quote_revisions(
    inspection_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lädt alle Quote-Revisionen für eine Besichtigung"""
    try:
        revisions = await inspection_service.get_quote_revisions_for_inspection(
            db=db,
            inspection_id=inspection_id
        )
        return revisions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fehler beim Laden der Quote-Revisionen: {str(e)}"
        )


@router.post("/quote-revisions/{revision_id}/confirm")
async def confirm_quote_revision(
    revision_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Bauträger bestätigt eine Quote-Revision (finale Entscheidung)"""
    try:
        success = await inspection_service.confirm_quote_revision(
            db=db,
            revision_id=revision_id,
            confirmed_by=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quote-Revision konnte nicht bestätigt werden"
            )
        
        # Belohne den Bauträger mit Credits für die Nutzung des vollständigen Prozesses
        # Hole die Revision um die inspection_id zu bekommen
        revision_result = await db.execute(
            select(QuoteRevision).where(QuoteRevision.id == revision_id)
        )
        revision = revision_result.scalar_one_or_none()
        
        if revision:
            await CreditService.reward_inspection_quote_acceptance(
                db=db,
                user_id=current_user.id,
                quote_id=revision.original_quote_id,
                inspection_id=revision.inspection_id
            )
            
        return {"message": "Quote-Revision erfolgreich bestätigt und Auftragsbestätigung versendet"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fehler beim Bestätigen: {str(e)}"
        )


@router.post("/quote-revisions/{revision_id}/reject")
async def reject_quote_revision(
    revision_id: int,
    rejection_reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Bauträger lehnt eine Quote-Revision ab"""
    try:
        success = await inspection_service.reject_quote_revision(
            db=db,
            revision_id=revision_id,
            rejected_by=current_user.id,
            rejection_reason=rejection_reason
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quote-Revision konnte nicht abgelehnt werden"
            )
            
        return {"message": "Quote-Revision abgelehnt"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fehler beim Ablehnen: {str(e)}"
        )


@router.post("/{inspection_id}/complete")
async def complete_inspection(
    inspection_id: int,
    completion_notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Markiert eine Besichtigung als abgeschlossen"""
    try:
        success = await inspection_service.complete_inspection(
            db=db,
            inspection_id=inspection_id,
            completion_notes=completion_notes
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Besichtigung konnte nicht abgeschlossen werden"
            )
            
        return {"message": "Besichtigung erfolgreich abgeschlossen"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fehler beim Abschließen: {str(e)}"
        )


@router.post("/{inspection_id}/cancel")
async def cancel_inspection(
    inspection_id: int,
    cancellation_reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Bricht eine Besichtigung ab"""
    try:
        success = await inspection_service.cancel_inspection(
            db=db,
            inspection_id=inspection_id,
            cancellation_reason=cancellation_reason
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Besichtigung konnte nicht abgebrochen werden"
            )
            
        return {"message": "Besichtigung abgebrochen"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fehler beim Abbrechen: {str(e)}"
        )


@router.get("/milestones/inspection-required")
async def get_inspection_required_milestones(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lädt alle Gewerke mit requires_inspection = True für den aktuellen Bauträger"""
    try:
        milestones = await inspection_service.get_inspection_required_milestones(
            db=db,
            user_id=current_user.id
        )
        return milestones
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fehler beim Laden der besichtigungspflichtigen Gewerke: {str(e)}"
        ) 