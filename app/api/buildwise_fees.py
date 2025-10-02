from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.buildwise_fee_service import BuildWiseFeeService
from app.services.stripe_service import StripePaymentService
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

@router.get("/test", response_model=dict)
async def test_buildwise_fees_endpoint():
    """
    Einfacher Test-Endpunkt für BuildWise-Gebühren
    """
    return {
        "message": "BuildWise-Gebühren API funktioniert",
        "status": "ok",
        "timestamp": "2024-01-01T00:00:00Z"
    }

@router.get("/")
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
    Holt alle BuildWise-Gebühren mit optionalen Filtern.
    
    Für Dienstleister: Zeigt nur eigene Gebühren
    Für Administratoren: Zeigt alle Gebühren
    """
    try:
        from ..models.user import UserRole
        
        print(f"[DEBUG] Lade BuildWise-Gebühren mit Parametern: skip={skip}, limit={limit}, project_id={project_id}, status={status}, month={month}, year={year}")
        print(f"   - Benutzer: {current_user.email} (Rolle: {current_user.user_role})")
        
        # Wenn Dienstleister, zeige nur eigene Gebühren
        if current_user.user_role == UserRole.DIENSTLEISTER:
            fees = await BuildWiseFeeService.get_fees_for_service_provider(
                db=db,
                service_provider_id=current_user.id,
                status=status
            )
            print(f"[SUCCESS] Debug: {len(fees)} Gebühren für Dienstleister {current_user.id} geladen")
        else:
            # Für Bauträger und Admins: Zeige alle oder gefilterte Gebühren
            fees = await BuildWiseFeeService.get_fees(
                db=db,
                skip=skip,
                limit=limit,
                project_id=project_id,
                status=status,
                month=month,
                year=year
            )
            print(f"[SUCCESS] Debug: {len(fees)} Gebühren erfolgreich geladen")
        
        # Lade Quote-Titel für alle Fees in einem separaten Query (eager loading)
        from ..models.quote import Quote
        from sqlalchemy import select as sql_select
        
        quote_titles = {}
        if fees and len(fees) > 0:
            quote_ids = [fee.quote_id for fee in fees if fee.quote_id]
            if quote_ids:
                try:
                    quotes_query = sql_select(Quote).where(Quote.id.in_(quote_ids))
                    quotes_result = await db.execute(quotes_query)
                    quotes = quotes_result.scalars().all()
                    quote_titles = {quote.id: quote.title for quote in quotes}
                    print(f"[DEBUG] {len(quote_titles)} Quote-Titel geladen")
                except Exception as e:
                    print(f"[WARNING] Fehler beim Laden der Quote-Titel: {e}")
        
        # Einfache JSON-Response ohne Pydantic-Validierung
        result = []
        for fee in fees:
            # Hole Quote-Titel aus dem vorgeladenen Dictionary
            quote_title = quote_titles.get(fee.quote_id, None)
            
            fee_dict = {
                "id": fee.id,
                "project_id": fee.project_id,
                "quote_id": fee.quote_id,
                "quote_title": quote_title,  # Neues Feld für den echten Ausschreibungsnamen
                "cost_position_id": fee.cost_position_id,
                "service_provider_id": fee.service_provider_id,
                "fee_amount": float(fee.fee_amount) if fee.fee_amount else 0.0,
                "fee_percentage": float(fee.fee_percentage) if fee.fee_percentage else 1.0,
                "quote_amount": float(fee.quote_amount) if fee.quote_amount else 0.0,
                "currency": fee.currency or "CHF",
                "invoice_number": fee.invoice_number,
                "invoice_date": fee.invoice_date.isoformat() if fee.invoice_date else None,
                "due_date": fee.due_date.isoformat() if fee.due_date else None,
                "payment_date": fee.payment_date.isoformat() if fee.payment_date else None,
                "status": fee.status or "open",
                "invoice_pdf_path": fee.invoice_pdf_path,
                "invoice_pdf_generated": fee.invoice_pdf_generated or False,
                "tax_rate": float(fee.tax_rate) if fee.tax_rate else 8.1,
                "tax_amount": float(fee.tax_amount) if fee.tax_amount else None,
                "net_amount": float(fee.net_amount) if fee.net_amount else None,
                "gross_amount": float(fee.gross_amount) if fee.gross_amount else None,
                "fee_details": fee.fee_details,
                "notes": fee.notes,
                "created_at": fee.created_at.isoformat() if fee.created_at else datetime.utcnow().isoformat(),
                "updated_at": fee.updated_at.isoformat() if fee.updated_at else datetime.utcnow().isoformat(),
            }
            result.append(fee_dict)
        
        return result
        
    except Exception as e:
        print(f"[ERROR] Debug: Fehler beim Laden der Gebühren: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Gebühren: {str(e)}")

@router.get("/statistics")
async def get_buildwise_fee_statistics(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Holt Statistiken für BuildWise-Gebühren
    Für Dienstleister: Zeigt nur eigene Gebühren-Statistiken
    Für Bauträger/Admins: Zeigt alle Statistiken
    """
    try:
        from ..models.user import UserRole
        
        print(f"[DEBUG] Lade BuildWise-Gebühren Statistiken...")
        print(f"   - Benutzer: {current_user.email} (Rolle: {current_user.user_role})")
        
        # Wenn Dienstleister, zeige nur eigene Statistiken
        service_provider_id = None
        if current_user.user_role == UserRole.DIENSTLEISTER:
            service_provider_id = current_user.id
            print(f"   - Filter: Nur Dienstleister {service_provider_id}")
        
        stats = await BuildWiseFeeService.get_statistics(db=db, service_provider_id=service_provider_id)
        print(f"[SUCCESS] Debug: Statistiken erfolgreich geladen")
        
        # Konvertiere zu einfachem Dict für JSON-Response
        result = {
            "total_fees": stats.total_fees,
            "total_amount": float(stats.total_amount),
            "total_paid": float(stats.total_paid),
            "total_open": float(stats.total_open),
            "total_overdue": float(stats.total_overdue),
            "monthly_breakdown": stats.monthly_breakdown,
            "status_breakdown": stats.status_breakdown
        }
        
        return result
        
    except Exception as e:
        print(f"[ERROR] Debug: Fehler beim Laden der Statistiken: {str(e)}")
        import traceback
        traceback.print_exc()
        # Fallback: Leere Statistiken zurückgeben
        return {
            "total_fees": 0,
            "total_amount": 0.0,
            "total_paid": 0.0,
            "total_open": 0.0,
            "total_overdue": 0.0,
            "monthly_breakdown": [],
            "status_breakdown": {}
        }

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

@router.post("/{fee_id}/generate-gewerk-invoice")
async def generate_gewerk_invoice(
    fee_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Generiert eine PDF-Rechnung für eine Gebühr (nur Gewerk-Daten) 
    und speichert sie automatisch als Dokument
    """
    try:
        result = await BuildWiseFeeService.generate_gewerk_invoice_and_save_document(
            db=db, 
            fee_id=fee_id, 
            current_user_id=current_user.id
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "document_id": result["document_id"],
                "document_path": result["document_path"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Generieren der Gewerk-Rechnung: {str(e)}")

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

@router.get("/check-account-status")
async def check_account_status(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Prüft ob der aktuelle Benutzer (Dienstleister) überfällige Rechnungen hat.
    Wenn ja, wird der Account als gesperrt markiert.
    """
    from ..models.user import UserRole
    from datetime import date
    
    # Nur für Dienstleister relevant
    if current_user.user_role != UserRole.DIENSTLEISTER:
        return {
            "account_locked": False,
            "has_overdue_fees": False,
            "overdue_fees": [],
            "message": "Nur für Dienstleister relevant"
        }
    
    try:
        print(f"[API] Prüfe Account-Status für Dienstleister {current_user.id}")
        
        # Hole alle Gebühren des Dienstleisters mit Status "overdue" oder "open"
        fees = await BuildWiseFeeService.get_fees_for_service_provider(
            db=db,
            service_provider_id=current_user.id,
            status=None  # Alle Status
        )
        
        print(f"[API] {len(fees)} Gebühren für Dienstleister {current_user.id} gefunden")
        
        # Filtere überfällige Gebühren
        today = date.today()
        overdue_fees = []
        
        for fee in fees:
            # Prüfe ob Gebühr überfällig ist
            if fee.status == 'overdue' or (fee.status == 'open' and fee.due_date and fee.due_date < today):
                overdue_fees.append({
                    "id": fee.id,
                    "invoice_number": fee.invoice_number,
                    "due_date": fee.due_date.isoformat() if fee.due_date else None,
                    "fee_amount": float(fee.fee_amount),
                    "gross_amount": float(fee.gross_amount) if fee.gross_amount else float(fee.fee_amount),
                    "currency": fee.currency,
                    "days_overdue": (today - fee.due_date).days if fee.due_date else 0,
                    "stripe_payment_link_url": fee.stripe_payment_link_url
                })
        
        # Account ist gesperrt wenn überfällige Gebühren existieren
        account_locked = len(overdue_fees) > 0
        
        return {
            "account_locked": account_locked,
            "has_overdue_fees": account_locked,
            "overdue_fees": overdue_fees,
            "total_overdue_amount": sum(f["gross_amount"] for f in overdue_fees),
            "message": "Account gesperrt - Bitte bezahlen Sie Ihre überfälligen Rechnungen" if account_locked else "Account aktiv"
        }
        
    except Exception as e:
        print(f"[ERROR] Fehler bei Account-Status-Prüfung: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Robuste Fehlerbehandlung - gib sicheren Fallback zurück statt 500 Fehler
        return {
            "account_locked": False,
            "has_overdue_fees": False,
            "overdue_fees": [],
            "total_overdue_amount": 0.0,
            "message": f"Account-Status konnte nicht geprüft werden: {str(e)}"
        }

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

# ============================================================================
# Stripe Payment Integration Endpoints
# ============================================================================

@router.post("/{fee_id}/create-payment-link")
async def create_payment_link(
    fee_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Erstellt einen Stripe Payment Link für eine BuildWise-Gebühr.
    
    Der Dienstleister wird zu einer Stripe-Checkout-Seite weitergeleitet,
    wo er die Gebühr bezahlen kann.
    """
    
    try:
        print(f"[API] Erstelle Payment Link für Gebühr {fee_id}")
        
        # Hole die Gebühr aus der Datenbank
        fee = await BuildWiseFeeService.get_fee(db=db, fee_id=fee_id)
        if not fee:
            raise HTTPException(status_code=404, detail="Gebühr nicht gefunden")
        
        # Prüfe ob Gebühr bereits bezahlt ist
        if fee.status == 'paid':
            raise HTTPException(
                status_code=400, 
                detail="Diese Gebühr wurde bereits bezahlt"
            )
        
        # Hinweis: Wir erstellen immer eine neue Checkout Session
        # (alte Payment Links werden nicht wiederverwendet, da sie expire können)
        print(f"[API] Erstelle neue Checkout Session für Gebühr {fee_id}")
        
        # Berechne Bruttobetrag (inkl. MwSt.)
        gross_amount = fee.gross_amount or fee.fee_amount
        
        # Erstelle Checkout Session über Stripe
        payment_link_data = StripePaymentService.create_payment_link(
            fee_id=fee.id,
            amount=gross_amount,
            currency=fee.currency.lower(),
            description=f"BuildWise Vermittlungsgebühr für Projekt {fee.project_id}",
            invoice_number=fee.invoice_number or f"BW-{fee.id:06d}",
            fee_percentage=float(fee.fee_percentage)
        )
        
        # Speichere Payment Link in der Datenbank
        fee.stripe_payment_link_id = payment_link_data["payment_link_id"]
        fee.stripe_payment_link_url = payment_link_data["payment_link_url"]
        
        await db.commit()
        await db.refresh(fee)
        
        print(f"[API] Payment Link erfolgreich erstellt und gespeichert")
        
        return {
            "success": True,
            "payment_link_url": payment_link_data["payment_link_url"],
            "payment_link_id": payment_link_data["payment_link_id"],
            "amount": float(gross_amount),
            "currency": fee.currency,
            "message": "Payment Link erfolgreich erstellt"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Fehler beim Erstellen des Payment Links: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Fehler beim Erstellen des Payment Links: {str(e)}"
        )

@router.get("/{fee_id}/payment-status")
async def get_payment_status(
    fee_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Holt den aktuellen Zahlungsstatus einer Gebühr.
    """
    
    try:
        fee = await BuildWiseFeeService.get_fee(db=db, fee_id=fee_id)
        if not fee:
            raise HTTPException(status_code=404, detail="Gebühr nicht gefunden")
        
        return {
            "fee_id": fee.id,
            "status": fee.status,
            "payment_link_id": fee.stripe_payment_link_id,
            "payment_link_url": fee.stripe_payment_link_url,
            "payment_intent_id": fee.stripe_payment_intent_id,
            "payment_date": fee.payment_date.isoformat() if fee.payment_date else None,
            "payment_method": fee.payment_method,
            "amount": float(fee.fee_amount),
            "gross_amount": float(fee.gross_amount) if fee.gross_amount else None,
            "currency": fee.currency
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Fehler beim Abrufen des Zahlungsstatus: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Abrufen des Zahlungsstatus: {str(e)}"
        )

@router.post("/stripe-webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook-Endpunkt für Stripe-Events.
    
    Wird von Stripe aufgerufen, wenn eine Zahlung erfolgreich ist.
    Markiert die Gebühr automatisch als bezahlt.
    """
    
    try:
        # Hole Payload und Signatur
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        print(f"[Webhook] Stripe Webhook erhalten")
        
        # Verifiziere Webhook-Signatur (wenn Secret konfiguriert)
        try:
            event = StripePaymentService.verify_webhook_signature(
                payload=payload,
                sig_header=sig_header
            )
        except ValueError as e:
            print(f"[Webhook] Ungültige Signatur: {str(e)}")
            raise HTTPException(status_code=400, detail="Ungültige Signatur")
        
        # Verarbeite Event
        event_type = event.get("type")
        print(f"[Webhook] Event Type: {event_type}")
        
        # Relevante Events für Payment Links:
        # - checkout.session.completed: Zahlung abgeschlossen
        # - payment_intent.succeeded: Payment Intent erfolgreich
        
        if event_type == "checkout.session.completed":
            # Zahlung wurde erfolgreich abgeschlossen
            try:
                payment_data = StripePaymentService.process_payment_success(event)
                
                fee_id = payment_data.get("fee_id")
                if not fee_id:
                    print("[Webhook] Keine fee_id in Metadaten gefunden - Event wird ignoriert")
                    return JSONResponse(
                        status_code=200,
                        content={"status": "ignored", "reason": "no_fee_id"}
                    )
                
                # Hole Gebühr aus Datenbank
                fee = await BuildWiseFeeService.get_fee(db=db, fee_id=fee_id)
                if not fee:
                    print(f"[Webhook] Gebühr {fee_id} nicht gefunden")
                    return JSONResponse(
                        status_code=200,  # 200 statt 404 - Stripe soll nicht erneut senden
                        content={"status": "error", "reason": "fee_not_found", "fee_id": fee_id}
                    )
                
                # Prüfe ob bereits bezahlt (Idempotenz)
                if fee.status == 'paid':
                    print(f"[Webhook] Gebühr {fee_id} ist bereits als bezahlt markiert - überspringe")
                    return JSONResponse(
                        status_code=200,
                        content={
                            "status": "already_processed",
                            "fee_id": fee_id,
                            "message": "Gebühr bereits als bezahlt markiert"
                        }
                    )
                
                # Markiere Gebühr als bezahlt
                from datetime import date
                fee.status = 'paid'
                fee.payment_date = date.today()
                fee.stripe_payment_intent_id = payment_data.get("payment_intent_id")
                fee.stripe_checkout_session_id = payment_data.get("session_id")
                fee.payment_method = payment_data.get("payment_method")
                
                await db.commit()
                await db.refresh(fee)
                
                print(f"[Webhook] ✅ Gebühr {fee_id} erfolgreich als bezahlt markiert")
                print(f"   - Betrag: {payment_data.get('amount_received')} {payment_data.get('currency')}")
                print(f"   - Zahlungsmethode: {payment_data.get('payment_method')}")
                print(f"   - Kunden-E-Mail: {payment_data.get('customer_email')}")
                
                # TODO: E-Mail-Benachrichtigung senden
                # await send_payment_confirmation_email(fee, payment_data)
                
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "fee_id": fee_id,
                        "amount": payment_data.get("amount_received"),
                        "currency": payment_data.get("currency"),
                        "payment_method": payment_data.get("payment_method"),
                        "message": "Gebühr erfolgreich als bezahlt markiert"
                    }
                )
                
            except Exception as e:
                print(f"[Webhook] Fehler bei checkout.session.completed Verarbeitung: {str(e)}")
                import traceback
                traceback.print_exc()
                return JSONResponse(
                    status_code=200,  # Immer 200 zurückgeben
                    content={"status": "error", "message": str(e)}
                )
        
        elif event_type == "payment_intent.succeeded":
            # Alternative: Payment Intent erfolgreich
            print(f"[Webhook] Payment Intent erfolgreich")
            # Optional: Zusätzliche Verarbeitung
            
        # Andere Events ignorieren
        return JSONResponse(
            status_code=200,
            content={"status": "received", "event_type": event_type}
        )
        
    except Exception as e:
        print(f"[Webhook] Fehler bei Webhook-Verarbeitung: {str(e)}")
        import traceback
        traceback.print_exc()
        # Gib 200 zurück, damit Stripe nicht erneut sendet
        return JSONResponse(
            status_code=200,
            content={"status": "error", "message": str(e)}
        ) 