#!/usr/bin/env python3
"""
Subscription Service für BuildWise
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ..models.user import User, SubscriptionPlan, SubscriptionStatus
from ..services.stripe_service import StripeService
from ..services.security_service import SecurityService
from ..models.audit_log import AuditAction

class SubscriptionService:
    """Service für Subscription-Management"""
    
    @staticmethod
    async def get_user_subscription(db: AsyncSession, user_id: int) -> Optional[Dict[str, Any]]:
        """Holt die Subscription-Daten eines Benutzers"""
        try:
            query = select(User).where(User.id == user_id)
            result = await db.execute(query)
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            return {
                'plan': user.subscription_plan.value if user.subscription_plan else 'basis',
                'status': user.subscription_status.value if user.subscription_status else 'inactive',
                'subscription_id': user.subscription_id,
                'customer_id': user.customer_id,
                'subscription_start': user.subscription_start,
                'subscription_end': user.subscription_end,
                'max_gewerke': user.max_gewerke or 3,
                'is_pro': user.subscription_plan == SubscriptionPlan.PRO and user.subscription_status == SubscriptionStatus.ACTIVE
            }
        except Exception as e:
            print(f"[ERROR] Fehler beim Holen der Subscription: {e}")
            return None
    
    @staticmethod
    async def create_stripe_customer(db: AsyncSession, user_id: int) -> Optional[str]:
        """Erstellt einen Stripe Customer für den Benutzer"""
        try:
            query = select(User).where(User.id == user_id)
            result = await db.execute(query)
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            # Prüfe ob bereits Customer vorhanden
            if user.customer_id:
                return user.customer_id
            
            # Erstelle neuen Stripe Customer
            customer_name = f"{user.first_name} {user.last_name}"
            customer = await StripeService.create_customer(user.email, customer_name)
            
            if not customer:
                return None
            
            # Speichere Customer ID
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(customer_id=customer['id'])
            )
            await db.commit()
            
            return customer['id']
        except Exception as e:
            print(f"[ERROR] Fehler beim Erstellen des Stripe Customer: {e}")
            return None
    
    @staticmethod
    async def create_checkout_session(
        db: AsyncSession, 
        user_id: int, 
        plan_type: str,  # 'monthly' oder 'yearly'
        success_url: str,
        cancel_url: str
    ) -> Optional[Dict[str, Any]]:
        """Erstellt eine Stripe Checkout Session"""
        try:
            # Hole oder erstelle Stripe Customer
            customer_id = await SubscriptionService.create_stripe_customer(db, user_id)
            if not customer_id:
                return None
            
            # Wähle Price ID basierend auf Plan
            if plan_type == 'monthly':
                price_id = StripeService.PRO_MONTHLY_PRICE_ID
            elif plan_type == 'yearly':
                price_id = StripeService.PRO_YEARLY_PRICE_ID
            else:
                return None
            
            # Erstelle Checkout Session
            session = await StripeService.create_checkout_session(
                customer_id=customer_id,
                price_id=price_id,
                success_url=success_url,
                cancel_url=cancel_url,
                user_id=user_id
            )
            
            return session
        except Exception as e:
            print(f"[ERROR] Fehler beim Erstellen der Checkout Session: {e}")
            return None
    
    @staticmethod
    async def activate_subscription(
        db: AsyncSession,
        user_id: int,
        subscription_id: str,
        customer_id: str,
        plan_type: str = 'pro'
    ) -> bool:
        """Aktiviert eine Subscription nach erfolgreicher Zahlung"""
        try:
            # Hole Subscription-Details von Stripe
            stripe_subscription = await StripeService.get_subscription(subscription_id)
            if not stripe_subscription:
                return False
            
            # Berechne Start- und End-Datum
            start_date = datetime.fromtimestamp(stripe_subscription['current_period_start'])
            end_date = datetime.fromtimestamp(stripe_subscription['current_period_end'])
            
            # Aktualisiere User-Daten
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    subscription_plan=SubscriptionPlan.PRO,
                    subscription_status=SubscriptionStatus.ACTIVE,
                    subscription_id=subscription_id,
                    customer_id=customer_id,
                    subscription_start=start_date,
                    subscription_end=end_date,
                    max_gewerke=-1  # Unbegrenzt für Pro
                )
            )
            await db.commit()
            
            # Audit Log
            await SecurityService.create_audit_log(
                db, user_id, AuditAction.USER_UPDATE,
                f"Subscription aktiviert: {plan_type} bis {end_date}",
                resource_type="subscription", resource_id=subscription_id
            )
            
            print(f"[SUCCESS] Subscription aktiviert für User {user_id}: {subscription_id}")
            return True
        except Exception as e:
            print(f"[ERROR] Fehler beim Aktivieren der Subscription: {e}")
            return False
    
    @staticmethod
    async def cancel_subscription(db: AsyncSession, user_id: int, immediate: bool = False) -> bool:
        """Kündigt eine Subscription"""
        try:
            query = select(User).where(User.id == user_id)
            result = await db.execute(query)
            user = result.scalar_one_or_none()
            
            if not user or not user.subscription_id:
                return False
            
            # Kündige bei Stripe
            success = await StripeService.cancel_subscription(
                user.subscription_id, 
                at_period_end=not immediate
            )
            
            if not success:
                return False
            
            # Aktualisiere Status
            if immediate:
                # Sofortige Kündigung
                await db.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(
                        subscription_status=SubscriptionStatus.CANCELED,
                        subscription_plan=SubscriptionPlan.BASIS,
                        max_gewerke=3
                    )
                )
            else:
                # Kündigung am Periodenende
                await db.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(subscription_status=SubscriptionStatus.CANCELED)
                )
            
            await db.commit()
            
            # Audit Log
            await SecurityService.create_audit_log(
                db, user_id, AuditAction.USER_UPDATE,
                f"Subscription gekündigt: {'sofort' if immediate else 'am Periodenende'}",
                resource_type="subscription", resource_id=user.subscription_id
            )
            
            print(f"[SUCCESS] Subscription gekündigt für User {user_id}")
            return True
        except Exception as e:
            print(f"[ERROR] Fehler beim Kündigen der Subscription: {e}")
            return False
    
    @staticmethod
    async def check_gewerke_limit(db: AsyncSession, user_id: int, project_id: int) -> Dict[str, Any]:
        """Prüft das Gewerke-Limit für einen Benutzer"""
        try:
            # Hole User-Daten
            query = select(User).where(User.id == user_id)
            result = await db.execute(query)
            user = result.scalar_one_or_none()
            
            if not user:
                return {'allowed': False, 'reason': 'User nicht gefunden'}
            
            # Pro-User haben unbegrenzte Gewerke
            if user.subscription_plan == SubscriptionPlan.PRO and user.subscription_status == SubscriptionStatus.ACTIVE:
                return {'allowed': True, 'limit': -1, 'current': 0}
            
            # Basis-User: Zähle aktuelle Gewerke (vereinfacht - hier würde normalerweise die Quote-Tabelle abgefragt)
            # Für jetzt nehmen wir an, dass das Limit 3 ist
            max_gewerke = user.max_gewerke or 3
            current_gewerke = 0  # TODO: Aus Quote-Tabelle holen
            
            if current_gewerke >= max_gewerke:
                return {
                    'allowed': False, 
                    'limit': max_gewerke, 
                    'current': current_gewerke,
                    'reason': f'Limit erreicht: {current_gewerke}/{max_gewerke} Gewerke'
                }
            
            return {
                'allowed': True, 
                'limit': max_gewerke, 
                'current': current_gewerke
            }
        except Exception as e:
            print(f"[ERROR] Fehler beim Prüfen des Gewerke-Limits: {e}")
            return {'allowed': False, 'reason': 'Fehler bei der Prüfung'}
    
    @staticmethod
    async def sync_subscription_from_stripe(db: AsyncSession, user_id: int) -> bool:
        """Synchronisiert Subscription-Status mit Stripe"""
        try:
            query = select(User).where(User.id == user_id)
            result = await db.execute(query)
            user = result.scalar_one_or_none()
            
            if not user or not user.subscription_id:
                return False
            
            # Hole aktuelle Daten von Stripe
            stripe_subscription = await StripeService.get_subscription(user.subscription_id)
            if not stripe_subscription:
                return False
            
            # Mappe Stripe Status zu unserem Status
            status_mapping = {
                'active': SubscriptionStatus.ACTIVE,
                'canceled': SubscriptionStatus.CANCELED,
                'incomplete': SubscriptionStatus.INACTIVE,
                'incomplete_expired': SubscriptionStatus.INACTIVE,
                'past_due': SubscriptionStatus.PAST_DUE,
                'unpaid': SubscriptionStatus.PAST_DUE,
                'trialing': SubscriptionStatus.ACTIVE
            }
            
            new_status = status_mapping.get(stripe_subscription['status'], SubscriptionStatus.INACTIVE)
            
            # Aktualisiere User-Daten
            updates = {
                'subscription_status': new_status,
                'subscription_start': datetime.fromtimestamp(stripe_subscription['current_period_start']),
                'subscription_end': datetime.fromtimestamp(stripe_subscription['current_period_end'])
            }
            
            # Setze Plan und Limits basierend auf Status
            if new_status == SubscriptionStatus.ACTIVE:
                updates['subscription_plan'] = SubscriptionPlan.PRO
                updates['max_gewerke'] = -1
            else:
                updates['subscription_plan'] = SubscriptionPlan.BASIS
                updates['max_gewerke'] = 3
            
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(**updates)
            )
            await db.commit()
            
            print(f"[SUCCESS] Subscription synchronisiert für User {user_id}: {new_status.value}")
            return True
        except Exception as e:
            print(f"[ERROR] Fehler beim Synchronisieren der Subscription: {e}")
            return False 