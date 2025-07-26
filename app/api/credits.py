from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging
from datetime import datetime

from ..core.database import get_db
from ..services.credit_service import CreditService
from ..schemas.user_credits import (
    CreditBalanceResponse, CreditSystemStatus, CreditAdjustmentRequest,
    CreditEventRead, CreditPurchaseRead, CreditPackageInfo
)
from ..api.deps import get_current_user
from ..models.user import User, UserRole
from ..models.credit_event import CreditEventType
from ..models.credit_purchase import CreditPackage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/credits", tags=["credits"])


@router.get("/balance", response_model=CreditBalanceResponse)
async def get_credit_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Holt den aktuellen Credit-Status des Benutzers"""
    
    try:
        balance = await CreditService.get_credit_balance(db, current_user.id)
        return balance
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Credit-Balance für User {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Abrufen der Credit-Balance"
        )


@router.get("/events", response_model=List[CreditEventRead])
async def get_credit_events(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Holt Credit-Events für den Benutzer"""
    
    try:
        events = await CreditService.get_credit_events(db, current_user.id, limit, offset)
        return events
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Credit-Events für User {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Abrufen der Credit-Events"
        )


@router.get("/packages", response_model=List[CreditPackageInfo])
async def get_credit_packages():
    """Holt verfügbare Credit-Packages"""
    
    try:
        packages = await CreditService.get_credit_packages()
        return packages
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Credit-Packages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Abrufen der Credit-Packages"
        )


@router.post("/purchase/initiate")
async def initiate_credit_purchase(
    package_type: CreditPackage,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Initiiert einen Credit-Kauf (erstellt Stripe-Session)"""
    
    try:
        # Prüfe ob User Bauträger ist
        if current_user.user_role != UserRole.BAUTRAEGER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Bauträger können Credits kaufen"
            )
        
        # TODO: Stripe-Integration implementieren
        # Für jetzt simulieren wir die Session-Erstellung
        stripe_session_id = f"session_{current_user.id}_{package_type.value}_{int(datetime.now().timestamp())}"
        
        purchase = await CreditService.create_credit_purchase(
            db=db,
            user_id=current_user.id,
            package_type=package_type,
            stripe_session_id=stripe_session_id,
            user_email=current_user.email
        )
        
        return {
            "purchase_id": purchase.id,
            "stripe_session_id": stripe_session_id,
            "package_type": package_type.value,
            "credits_amount": purchase.credits_amount,
            "price_chf": purchase.price_chf,
            "checkout_url": f"/checkout/{stripe_session_id}"  # TODO: Echte Stripe-URL
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Initiieren des Credit-Kaufs für User {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Initiieren des Credit-Kaufs"
        )


@router.post("/webhook/stripe")
async def stripe_webhook(
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """Stripe Webhook für Credit-Käufe"""
    
    try:
        # TODO: Stripe-Webhook-Signatur validieren
        event_type = request.get("type")
        data = request.get("data", {})
        
        if event_type == "checkout.session.completed":
            session_id = data.get("object", {}).get("id")
            payment_intent_id = data.get("object", {}).get("payment_intent")
            
            if session_id:
                success = await CreditService.complete_credit_purchase(
                    db=db,
                    stripe_session_id=session_id,
                    stripe_payment_intent_id=payment_intent_id
                )
                
                if success:
                    return {"status": "success", "message": "Credit-Purchase abgeschlossen"}
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Credit-Purchase konnte nicht abgeschlossen werden"
                    )
        
        return {"status": "ignored", "message": "Event nicht verarbeitet"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler im Stripe-Webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler im Stripe-Webhook"
        )


# Admin-Endpunkte
@router.post("/admin/adjust", response_model=CreditSystemStatus)
async def admin_adjust_credits(
    adjustment: CreditAdjustmentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Manuelle Credit-Anpassung"""
    
    try:
        # Prüfe Admin-Berechtigung
        if current_user.user_role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Admins können Credits manuell anpassen"
            )
        
        success = await CreditService.manual_credit_adjustment(
            db=db,
            adjustment_request=adjustment,
            admin_user_id=current_user.id
        )
        
        if success:
            return CreditSystemStatus(
                status="success",
                message=f"Credits für User {adjustment.user_id} angepasst: {adjustment.credits_change}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credit-Anpassung fehlgeschlagen"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler bei manueller Credit-Anpassung: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler bei Credit-Anpassung"
        )


@router.post("/admin/daily-deduction", response_model=CreditSystemStatus)
async def admin_process_daily_deductions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Manueller Auslöser für tägliche Credit-Abzüge"""
    
    try:
        # Prüfe Admin-Berechtigung
        if current_user.user_role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Admins können tägliche Abzüge manuell auslösen"
            )
        
        result = await CreditService.process_all_daily_deductions(db)
        
        return CreditSystemStatus(
            status="success",
            message=f"Tägliche Abzüge verarbeitet: {result['processed_users']} User, {result['downgraded_users']} downgraded"
        )
        
    except Exception as e:
        logger.error(f"Fehler bei manuellen täglichen Abzügen: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler bei täglichen Abzügen"
        ) 