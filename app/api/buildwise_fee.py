from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from decimal import Decimal

from app.core.database import get_db
from app.core.config import settings
from app.services.buildwise_fee_service import BuildWiseFeeService
from app.schemas.buildwise_fee import (
    BuildWiseFeeCreate, 
    BuildWiseFeeUpdate, 
    BuildWiseFeeResponse,
    BuildWiseFeeStatistics,
    BuildWiseFeeConfigResponse,
    BuildWiseFeeConfigUpdate
)
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/config", response_model=BuildWiseFeeConfigResponse)
async def get_fee_config():
    """Gibt die aktuelle BuildWise-Gebühren-Konfiguration zurück."""
    return BuildWiseFeeConfigResponse(
        fee_percentage=settings.buildwise_fee_percentage,
        fee_phase=settings.buildwise_fee_phase,
        fee_enabled=settings.buildwise_fee_enabled
    )

@router.put("/config", response_model=BuildWiseFeeConfigResponse)
async def update_fee_config(
    config: BuildWiseFeeConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Aktualisiert die BuildWise-Gebühren-Konfiguration (nur für Admins)."""
    
    # Prüfe Admin-Berechtigung
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur Administratoren können die Gebühren-Konfiguration ändern"
        )
    
    # Validiere Eingaben
    if config.fee_percentage < 0 or config.fee_percentage > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gebühren-Prozentsatz muss zwischen 0 und 100 liegen"
        )
    
    if config.fee_phase not in ["beta", "production"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gebühren-Phase muss 'beta' oder 'production' sein"
        )
    
    # Aktualisiere Konfiguration
    settings.buildwise_fee_percentage = config.fee_percentage
    settings.buildwise_fee_phase = config.fee_phase
    settings.buildwise_fee_enabled = config.fee_enabled
    
    return BuildWiseFeeConfigResponse(
        fee_percentage=settings.buildwise_fee_percentage,
        fee_phase=settings.buildwise_fee_phase,
        fee_enabled=settings.buildwise_fee_enabled
    )

@router.get("/", response_model=List[BuildWiseFeeResponse])
async def get_buildwise_fees(
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Holt BuildWise-Gebühren mit optionalen Filtern (öffentlich für Service Provider)."""
    
    fees = await BuildWiseFeeService.get_fees(
        db=db,
        skip=skip,
        limit=limit,
        project_id=project_id,
        status=status,
        month=month,
        year=year
    )
    
    return [BuildWiseFeeResponse.model_validate(fee) for fee in fees]

@router.get("/statistics", response_model=BuildWiseFeeStatistics)
async def get_fee_statistics(
    db: AsyncSession = Depends(get_db)
):
    """Holt Statistiken für BuildWise-Gebühren (öffentlich für Service Provider)."""
    
    statistics = await BuildWiseFeeService.get_statistics(db)
    return statistics

@router.post("/create-from-quote/{quote_id}/{cost_position_id}")
async def create_fee_from_quote(
    quote_id: int,
    cost_position_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Erstellt eine BuildWise-Gebühr aus einem akzeptierten Angebot."""
    
    try:
        fee = await BuildWiseFeeService.create_fee_from_quote(
            db=db,
            quote_id=quote_id,
            cost_position_id=cost_position_id
        )
        return {"message": "BuildWise-Gebühr erfolgreich erstellt", "fee_id": fee.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Erstellen der Gebühr: {str(e)}")

@router.get("/{fee_id}", response_model=BuildWiseFeeResponse)
async def get_fee(
    fee_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Holt eine spezifische BuildWise-Gebühr (öffentlich für Service Provider)."""
    
    fee = await BuildWiseFeeService.get_fee(db, fee_id)
    if not fee:
        raise HTTPException(status_code=404, detail="Gebühr nicht gefunden")
    
    return BuildWiseFeeResponse.model_validate(fee)

@router.put("/{fee_id}", response_model=BuildWiseFeeResponse)
async def update_fee(
    fee_id: int,
    fee_data: BuildWiseFeeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Aktualisiert eine BuildWise-Gebühr (nur für Admins)."""
    
    # Prüfe Admin-Berechtigung
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur Administratoren können Gebühren bearbeiten"
        )
    
    fee = await BuildWiseFeeService.update_fee(db, fee_id, fee_data)
    if not fee:
        raise HTTPException(status_code=404, detail="Gebühr nicht gefunden")
    
    return BuildWiseFeeResponse.model_validate(fee)

@router.post("/{fee_id}/mark-as-paid")
async def mark_fee_as_paid(
    fee_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Markiert eine Gebühr als bezahlt (nur für Admins)."""
    
    # Prüfe Admin-Berechtigung
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur Administratoren können Gebühren als bezahlt markieren"
        )
    
    fee = await BuildWiseFeeService.mark_as_paid(db, fee_id)
    if not fee:
        raise HTTPException(status_code=404, detail="Gebühr nicht gefunden")
    
    return {"message": "Gebühr erfolgreich als bezahlt markiert"}

@router.post("/{fee_id}/generate-invoice")
async def generate_invoice(
    fee_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generiert eine PDF-Rechnung für eine Gebühr (nur für Admins)."""
    
    # Prüfe Admin-Berechtigung
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur Administratoren können Rechnungen generieren"
        )
    
    success = await BuildWiseFeeService.generate_invoice(db, fee_id)
    if not success:
        raise HTTPException(status_code=500, detail="Fehler beim Generieren der Rechnung")
    
    return {"message": "Rechnung erfolgreich generiert"}

@router.delete("/{fee_id}")
async def delete_fee(
    fee_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Löscht eine BuildWise-Gebühr (nur für Admins)."""
    
    # Prüfe Admin-Berechtigung
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur Administratoren können Gebühren löschen"
        )
    
    success = await BuildWiseFeeService.delete_fee(db, fee_id)
    if not success:
        raise HTTPException(status_code=404, detail="Gebühr nicht gefunden")
    
    return {"message": "Gebühr erfolgreich gelöscht"} 