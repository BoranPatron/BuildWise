from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from decimal import Decimal

from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.buildwise_fee_service import BuildWiseFeeService
from app.schemas.buildwise_fee import (
    BuildWiseFee, 
    BuildWiseFeeCreate, 
    BuildWiseFeeUpdate,
    BuildWiseFeeStatistics,
    BuildWiseFeeList
)

router = APIRouter(prefix="/buildwise-fees", tags=["BuildWise Fees"])

@router.post("/create-from-quote/{quote_id}/{cost_position_id}", response_model=BuildWiseFee)
async def create_fee_from_quote(
    quote_id: int,
    cost_position_id: int,
    fee_percentage: Optional[float] = Query(1.0, ge=0, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Erstellt automatisch eine BuildWise-Gebühr basierend auf einem akzeptierten Angebot
    """
    try:
        # Fallback falls None
        percentage = fee_percentage if fee_percentage is not None else 1.0
        fee = await BuildWiseFeeService.create_fee_from_quote(
            db=db,
            quote_id=quote_id,
            cost_position_id=cost_position_id,
            fee_percentage=percentage
        )
        return fee
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Erstellen der Gebühr: {str(e)}")

@router.get("/", response_model=List[BuildWiseFee])
async def get_buildwise_fees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    project_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2020, le=2030),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Holt alle BuildWise-Gebühren mit optionalen Filtern
    """
    fees = await BuildWiseFeeService.get_fees(
        db=db,
        skip=skip,
        limit=limit,
        project_id=project_id,
        status=status,
        month=month,
        year=year
    )
    return fees

@router.get("/statistics", response_model=BuildWiseFeeStatistics)
async def get_buildwise_fee_statistics(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Holt Statistiken für BuildWise-Gebühren
    """
    return await BuildWiseFeeService.get_statistics(db=db)

@router.get("/{fee_id}", response_model=BuildWiseFee)
async def get_buildwise_fee(
    fee_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Holt eine spezifische BuildWise-Gebühr
    """
    fee = await BuildWiseFeeService.get_fee(db=db, fee_id=fee_id)
    if not fee:
        raise HTTPException(status_code=404, detail="Gebühr nicht gefunden")
    return fee

@router.put("/{fee_id}", response_model=BuildWiseFee)
async def update_buildwise_fee(
    fee_id: int,
    fee_update: BuildWiseFeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Aktualisiert eine BuildWise-Gebühr
    """
    fee = await BuildWiseFeeService.update_fee(db=db, fee_id=fee_id, fee_data=fee_update)
    if not fee:
        raise HTTPException(status_code=404, detail="Gebühr nicht gefunden")
    return fee

@router.post("/{fee_id}/mark-as-paid", response_model=BuildWiseFee)
async def mark_fee_as_paid(
    fee_id: int,
    payment_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Markiert eine Gebühr als bezahlt
    """
    from datetime import datetime
    payment_date_obj = None
    if payment_date:
        try:
            payment_date_obj = datetime.strptime(payment_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Ungültiges Datumsformat. Verwenden Sie YYYY-MM-DD")
    fee = await BuildWiseFeeService.mark_as_paid(
        db=db, 
        fee_id=fee_id, 
        payment_date=payment_date_obj
    )
    if not fee:
        raise HTTPException(status_code=404, detail="Gebühr nicht gefunden")
    return fee

@router.post("/{fee_id}/generate-invoice")
async def generate_invoice(
    fee_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Generiert eine PDF-Rechnung für eine Gebühr
    """
    async def generate_pdf_task():
        await BuildWiseFeeService.generate_invoice(db=db, fee_id=fee_id)
    background_tasks.add_task(generate_pdf_task)
    return {"message": "PDF-Rechnung wird im Hintergrund generiert"}

@router.get("/{fee_id}/download-invoice")
async def download_invoice(
    fee_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Lädt eine PDF-Rechnung herunter
    """
    fee = await BuildWiseFeeService.get_fee(db=db, fee_id=fee_id)
    if not fee:
        raise HTTPException(status_code=404, detail="Gebühr nicht gefunden")
    # Extrahiere Werte korrekt
    invoice_pdf_generated = bool(getattr(fee, 'invoice_pdf_generated', False))
    invoice_pdf_path = getattr(fee, 'invoice_pdf_path', None)
    if not invoice_pdf_generated or not invoice_pdf_path:
        raise HTTPException(status_code=404, detail="PDF-Rechnung noch nicht generiert")
    return {
        "download_url": f"/api/v1/buildwise-fees/{fee_id}/invoice.pdf",
        "filename": f"buildwise_invoice_{fee.invoice_number}.pdf"
    }

@router.get("/{fee_id}/invoice.pdf")
async def serve_invoice_pdf(
    fee_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Serviert die PDF-Rechnung direkt
    """
    from fastapi.responses import FileResponse
    import os
    
    fee = await BuildWiseFeeService.get_fee(db=db, fee_id=fee_id)
    if not fee:
        raise HTTPException(status_code=404, detail="Gebühr nicht gefunden")
    
    invoice_pdf_generated = bool(getattr(fee, 'invoice_pdf_generated', False))
    invoice_pdf_path = getattr(fee, 'invoice_pdf_path', None)
    
    if not invoice_pdf_generated or not invoice_pdf_path:
        raise HTTPException(status_code=404, detail="PDF-Rechnung noch nicht generiert")
    
    # Prüfe ob Datei existiert
    if not os.path.exists(invoice_pdf_path):
        raise HTTPException(status_code=404, detail="PDF-Datei nicht gefunden")
    
    # Serviere PDF-Datei
    return FileResponse(
        path=invoice_pdf_path,
        media_type='application/pdf',
        filename=f"buildwise_invoice_{fee.invoice_number}.pdf"
    )

@router.post("/check-overdue")
async def check_overdue_fees(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Prüft auf überfällige Gebühren und markiert sie entsprechend
    """
    result = await BuildWiseFeeService.check_overdue_fees(db=db)
    return result

@router.get("/monthly/{month}/{year}", response_model=List[BuildWiseFee])
async def get_monthly_fees(
    month: int,
    year: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Holt Gebühren für einen spezifischen Monat
    """
    fees = await BuildWiseFeeService.get_fees(
        db=db,
        month=month,
        year=year
    )
    return fees

@router.delete("/{fee_id}")
async def delete_buildwise_fee(
    fee_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Löscht eine BuildWise-Gebühr (nur für Administratoren)
    """
    # TODO: Implementiere Admin-Berechtigung
    fee = await BuildWiseFeeService.get_fee(db=db, fee_id=fee_id)
    if not fee:
        raise HTTPException(status_code=404, detail="Gebühr nicht gefunden")
    await BuildWiseFeeService.delete_fee(db=db, fee_id=fee_id)
    return {"message": "Gebühr erfolgreich gelöscht"} 