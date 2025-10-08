#!/usr/bin/env python3
"""
Subscription API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from ..core.database import get_db
from ..api.deps import get_current_user
from ..services.subscription_service import SubscriptionService
from ..services.stripe_service import StripeService
from ..models.user import UserRole

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


class CreateCheckoutRequest(BaseModel):
    plan_type: str  # 'monthly' oder 'yearly'


class CancelSubscriptionRequest(BaseModel):
    immediate: bool = False


@router.get("/status")
async def get_subscription_status(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Holt den aktuellen Subscription-Status des Benutzers"""
    
    subscription = await SubscriptionService.get_user_subscription(db, current_user.id)
    
    if not subscription:
        return {
            'plan': 'basis',
            'status': 'inactive',
            'max_gewerke': 3,
            'is_pro': False
        }
    
    return subscription


@router.post("/create-checkout")
async def create_checkout_session(
    request: CreateCheckoutRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Erstellt eine Stripe Checkout Session für Pro-Upgrade"""
    
    # Nur Bauträger können upgraden
    if current_user.user_role != UserRole.BAUTRAEGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur Bauträger können Pro-Abonnements abschließen"
        )
    
    # Validiere Plan-Typ
    if request.plan_type not in ['monthly', 'yearly']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültiger Plan-Typ. Wählen Sie 'monthly' oder 'yearly'"
        )
    
    try:
        # URLs für Success und Cancel
        base_url = "http://localhost:5173"  # TODO: Aus Config laden
        success_url = f"{base_url}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{base_url}/subscription/canceled"
        
        # Erstelle Checkout Session
        session = await SubscriptionService.create_checkout_session(
            db=db,
            user_id=current_user.id,
            plan_type=request.plan_type,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Fehler beim Erstellen der Checkout Session"
            )
        
        return {
            'checkout_url': session['url'],
            'session_id': session['id']
        }
        
    except Exception as e:
        print(f"[ERROR] Checkout Session Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Erstellen der Checkout Session"
        )


@router.post("/cancel")
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Kündigt die aktuelle Subscription"""
    
    try:
        success = await SubscriptionService.cancel_subscription(
            db=db,
            user_id=current_user.id,
            immediate=request.immediate
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subscription konnte nicht gekündigt werden"
            )
        
        return {
            'message': 'Subscription erfolgreich gekündigt',
            'immediate': request.immediate
        }
        
    except Exception as e:
        print(f"[ERROR] Cancel Subscription Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Kündigen der Subscription"
        )


@router.post("/sync")
async def sync_subscription(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Synchronisiert Subscription-Status mit Stripe"""
    
    try:
        success = await SubscriptionService.sync_subscription_from_stripe(
            db=db,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subscription konnte nicht synchronisiert werden"
            )
        
        # Hole aktuelle Subscription-Daten
        subscription = await SubscriptionService.get_user_subscription(db, current_user.id)
        
        return {
            'message': 'Subscription erfolgreich synchronisiert',
            'subscription': subscription
        }
        
    except Exception as e:
        print(f"[ERROR] Sync Subscription Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Synchronisieren der Subscription"
        )


@router.get("/check-gewerke-limit/{project_id}")
async def check_gewerke_limit(
    project_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Prüft das Gewerke-Limit für einen Benutzer"""
    
    try:
        limit_check = await SubscriptionService.check_gewerke_limit(
            db=db,
            user_id=current_user.id,
            project_id=project_id
        )
        
        return limit_check
        
    except Exception as e:
        print(f"[ERROR] Check Gewerke Limit Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Prüfen des Gewerke-Limits"
        )


@router.get("/pricing")
async def get_pricing():
    """Gibt die Preis-Informationen zurück"""
    
    return {
        'plans': {
            'basis': {
                'name': 'BuildWise Basis',
                'price': 0,
                'currency': 'CHF',
                'interval': 'forever',
                'features': [
                    'Maximal 3 Gewerke-Ausschreibungen',
                    'Basis Dashboard-Funktionen',
                    'Standard Support'
                ],
                'limits': {
                    'max_gewerke': 3,
                    'dashboard_cards': ['manager', 'gewerke', 'docs']
                }
            },
            'pro_monthly': {
                'name': 'BuildWise Pro Monthly',
                'price': 12.99,
                'currency': 'CHF',
                'interval': 'month',
                'features': [
                    'Unbegrenzte Gewerke-Ausschreibungen',
                    'Alle Dashboard-Funktionen',
                    'Email & Kalender Integration',
                    'Priority Support'
                ],
                'limits': {
                    'max_gewerke': -1,
                    'dashboard_cards': 'all'
                }
            },
            'pro_yearly': {
                'name': 'BuildWise Pro Yearly',
                'price': 130.00,
                'currency': 'CHF',
                'interval': 'year',
                'savings': 16,
                'features': [
                    'Unbegrenzte Gewerke-Ausschreibungen',
                    'Alle Dashboard-Funktionen',
                    'Email & Kalender Integration',
                    'Priority Support',
                    '16% Ersparnis gegenüber monatlich'
                ],
                'limits': {
                    'max_gewerke': -1,
                    'dashboard_cards': 'all'
                }
            }
        }
    } 