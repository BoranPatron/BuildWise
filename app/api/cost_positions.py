from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models import User
from ..schemas.cost_position import (
    CostPositionCreate, CostPositionRead, CostPositionUpdate, 
    CostPositionSummary, CostPositionStatistics, CostPositionListItem
)
from ..services.cost_position_service import (
    create_cost_position, get_cost_position_by_id, get_cost_positions_for_invoice,
    update_cost_position, delete_cost_position, get_cost_position_statistics,
    get_cost_position_by_quote_id, get_cost_positions_for_project
)

router = APIRouter(prefix="/cost-positions", tags=["cost-positions"])
@router.get("/project/{project_id}", response_model=List[CostPositionListItem])
async def read_cost_positions_for_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt alle Kostenpositionen eines Projekts (über verknüpfte Rechnungen)"""
    positions = await get_cost_positions_for_project(db, project_id)
    return positions


@router.delete("/debug/delete-all-cost-positions")
async def delete_all_cost_positions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Debug-Endpoint zum Löschen aller Kostenpositionen"""
    try:
        # Prüfe ob User ein Admin oder Bauträger ist
        from ..models.user import UserRole
        if not (current_user.user_role == UserRole.ADMIN or current_user.user_role == UserRole.BAUTRAEGER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Admins und Bauträger können alle Kostenpositionen löschen"
            )
        
        # Lösche alle Kostenpositionen
        from sqlalchemy import text
        await db.execute(text("DELETE FROM cost_positions"))
        await db.commit()
        
        return {"message": "Alle Kostenpositionen wurden gelöscht"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Löschen der Kostenpositionen: {str(e)}"
        )


@router.post("/", response_model=CostPositionRead, status_code=status.HTTP_201_CREATED)
async def create_new_cost_position(
    cost_position_in: CostPositionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Erstellt eine neue Kostenposition für eine Rechnung"""
    cost_position = await create_cost_position(db, cost_position_in)
    return cost_position


@router.get("/invoice/{invoice_id}", response_model=List[CostPositionSummary])
async def read_cost_positions_for_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt alle Kostenpositionen für eine Rechnung"""
    cost_positions = await get_cost_positions_for_invoice(db, invoice_id)
    return cost_positions


@router.get("/{cost_position_id}", response_model=CostPositionRead)
async def read_cost_position(
    cost_position_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt eine spezifische Kostenposition"""
    cost_position = await get_cost_position_by_id(db, cost_position_id)
    if not cost_position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kostenposition nicht gefunden"
        )
    return cost_position


@router.put("/{cost_position_id}", response_model=CostPositionRead)
async def update_cost_position_endpoint(
    cost_position_id: int,
    cost_position_update: CostPositionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Aktualisiert eine Kostenposition"""
    cost_position = await get_cost_position_by_id(db, cost_position_id)
    if not cost_position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kostenposition nicht gefunden"
        )
    
    updated_cost_position = await update_cost_position(db, cost_position_id, cost_position_update)
    return updated_cost_position


@router.delete("/{cost_position_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cost_position_endpoint(
    cost_position_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Löscht eine Kostenposition"""
    success = await delete_cost_position(db, cost_position_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kostenposition nicht gefunden"
        )


@router.get("/invoice/{invoice_id}/statistics", response_model=CostPositionStatistics)
async def get_invoice_cost_position_statistics(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt Statistiken für Kostenpositionen einer Rechnung"""
    statistics = await get_cost_position_statistics(db, invoice_id)
    return statistics


# Legacy-Endpunkt für Abwärtskompatibilität
@router.get("/quote/{quote_id}")
async def get_cost_position_by_quote_id_endpoint(
    quote_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt Kostenpositionen für ein Angebot (Legacy-Funktion)"""
    cost_positions = await get_cost_position_by_quote_id(db, quote_id)
    return cost_positions 