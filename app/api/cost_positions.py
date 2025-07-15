from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models import User, CostCategory, CostStatus
from ..schemas.cost_position import (
    CostPositionCreate, CostPositionRead, CostPositionUpdate, 
    CostPositionSummary, CostPositionStatistics
)
from ..services.cost_position_service import (
    create_cost_position, get_cost_position_by_id, get_cost_positions_for_project,
    update_cost_position, delete_cost_position, get_cost_position_statistics,
    get_cost_positions_by_category, get_cost_positions_by_status,
    update_cost_position_progress, record_payment,
    get_cost_positions_from_accepted_quotes, get_cost_position_statistics_for_accepted_quotes
)

router = APIRouter(prefix="/cost-positions", tags=["cost-positions"])


@router.post("/", response_model=CostPositionRead, status_code=status.HTTP_201_CREATED)
async def create_new_cost_position(
    cost_position_in: CostPositionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Erstellt eine neue Kostenposition"""
    cost_position = await create_cost_position(db, cost_position_in)
    return cost_position


@router.get("/", response_model=List[CostPositionSummary])
async def read_cost_positions(
    project_id: int,
    category: Optional[CostCategory] = None,
    status: Optional[CostStatus] = None,
    accepted_quotes_only: bool = Query(True, description="Nur Kostenpositionen aus akzeptierten Angeboten"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt alle Kostenpositionen für ein Projekt"""
    if accepted_quotes_only:
        # Nur Kostenpositionen aus akzeptierten Angeboten
        cost_positions = await get_cost_positions_from_accepted_quotes(db, project_id)
        
        # Filtere nach Kategorie und Status falls angegeben
        if category:
            cost_positions = [cp for cp in cost_positions if cp.category == category]
        if status:
            cost_positions = [cp for cp in cost_positions if cp.status == status]
    else:
        # Alle Kostenpositionen (für Admin-Zwecke)
        if category:
            cost_positions = await get_cost_positions_by_category(db, project_id, category)
        elif status:
            cost_positions = await get_cost_positions_by_status(db, project_id, status)
        else:
            cost_positions = await get_cost_positions_for_project(db, project_id)
    
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
    cost_position = await get_cost_position_by_id(db, cost_position_id)
    if not cost_position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kostenposition nicht gefunden"
        )
    
    success = await delete_cost_position(db, cost_position_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kostenposition konnte nicht gelöscht werden"
        )
    
    return None


@router.get("/project/{project_id}/statistics", response_model=CostPositionStatistics)
async def get_project_cost_position_statistics(
    project_id: int,
    accepted_quotes_only: bool = Query(True, description="Nur Statistiken für akzeptierte Angebote"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt Statistiken für Kostenpositionen eines Projekts"""
    if accepted_quotes_only:
        stats = await get_cost_position_statistics_for_accepted_quotes(db, project_id)
    else:
        stats = await get_cost_position_statistics(db, project_id)
    return stats


@router.post("/{cost_position_id}/progress")
async def update_progress_endpoint(
    cost_position_id: int,
    progress_percentage: float = Query(..., ge=0, le=100, description="Fortschritt in Prozent"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Aktualisiert den Fortschritt einer Kostenposition"""
    cost_position = await get_cost_position_by_id(db, cost_position_id)
    if not cost_position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kostenposition nicht gefunden"
        )
    
    updated_cost_position = await update_cost_position_progress(db, cost_position_id, progress_percentage)
    return {
        "message": f"Fortschritt auf {progress_percentage}% aktualisiert",
        "cost_position_id": cost_position_id,
        "progress_percentage": progress_percentage
    }


@router.post("/{cost_position_id}/payment")
async def record_payment_endpoint(
    cost_position_id: int,
    payment_amount: float = Query(..., gt=0, description="Zahlungsbetrag"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Zeichnet eine Zahlung für eine Kostenposition auf"""
    cost_position = await get_cost_position_by_id(db, cost_position_id)
    if not cost_position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kostenposition nicht gefunden"
        )
    
    updated_cost_position = await record_payment(db, cost_position_id, payment_amount)
    if not updated_cost_position:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Aufzeichnen der Zahlung"
        )
    
    return {
        "message": f"Zahlung von {payment_amount} EUR aufgezeichnet",
        "cost_position_id": cost_position_id,
        "payment_amount": payment_amount,
        "total_paid": updated_cost_position.paid_amount
    } 