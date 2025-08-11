from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
import logging

from ..models.user_credits import UserCredits, PlanStatus
from ..models.credit_event import CreditEvent, CreditEventType
from ..models.credit_purchase import CreditPurchase, CreditPackage, PurchaseStatus
from ..models.user import User, UserRole, SubscriptionPlan, SubscriptionStatus
from ..schemas.user_credits import (
    UserCreditsCreate, UserCreditsUpdate, UserCreditsRead,
    CreditBalanceResponse, CreditSystemStatus, CreditAdjustmentRequest
)
from ..services.security_service import SecurityService
from ..models.audit_log import AuditAction

logger = logging.getLogger(__name__)


class CreditService:
    """Service für das BuildWise Credit-System"""
    
    # Credit-Rewards für verschiedene Aktionen
    CREDIT_REWARDS = {
        CreditEventType.QUOTE_ACCEPTED: 5,      # Angebot angenommen
        CreditEventType.INVOICE_RECEIVED: 3,     # Rechnung erhalten
        CreditEventType.PROJECT_COMPLETED: 10,   # Projekt abgeschlossen
        CreditEventType.PROVIDER_REVIEW: 2,      # Dienstleister bewertet
        CreditEventType.MILESTONE_COMPLETED: 3,  # Meilenstein abgeschlossen
        CreditEventType.DOCUMENT_UPLOADED: 1,    # Dokument hochgeladen
        CreditEventType.EXPENSE_ADDED: 1,        # Ausgabe hinzugefügt
        CreditEventType.REGISTRATION_BONUS: 100, # Registrierungs-Bonus
        CreditEventType.REFERRAL_BONUS: 20,      # Empfehlungs-Bonus
        CreditEventType.LOYALTY_BONUS: 10,       # Treue-Bonus
        CreditEventType.INSPECTION_QUOTE_ACCEPTED: 15,  # Angebot nach Besichtigung angenommen (Bonus!)
    }
    
    # Täglicher Credit-Abzug für Pro-Status
    DAILY_CREDIT_DEDUCTION = 1
    
    # Warnung bei niedrigen Credits
    LOW_CREDIT_WARNING_THRESHOLD = 10
    
    @staticmethod
    async def get_or_create_user_credits(
        db: AsyncSession, 
        user_id: int
    ) -> UserCredits:
        """Holt oder erstellt UserCredits für einen Benutzer"""
        
        # Prüfe ob UserCredits bereits existiert
        result = await db.execute(
            select(UserCredits).where(UserCredits.user_id == user_id)
        )
        user_credits = result.scalar_one_or_none()
        
        if not user_credits:
            # Erstelle neue UserCredits mit Willkommensbonus
            user_credits = UserCredits(
                user_id=user_id,
                credits=90,  # Willkommensbonus: 90 Credits
                plan_status=PlanStatus.PRO,
                pro_start_date=datetime.now()
            )
            db.add(user_credits)
            await db.flush()
            await db.commit()
            await db.refresh(user_credits)
            
            # Erstelle Registrierungs-Bonus Event
            await CreditService.create_credit_event(
                db=db,
                user_credits_id=user_credits.id,
                event_type=CreditEventType.REGISTRATION_BONUS,
                credits_change=90,
                description="🎉 Willkommensbonus! 90 Credits für Ihren Start mit BuildWise Pro",
                ip_address=None
            )
            
            logger.info(f"UserCredits für User {user_id} erstellt mit 90 Credits Willkommensbonus")
        
        return user_credits
    
    @staticmethod
    async def get_credit_balance(
        db: AsyncSession, 
        user_id: int
    ) -> CreditBalanceResponse:
        """Holt den aktuellen Credit-Status eines Benutzers"""
        
        user_credits = await CreditService.get_or_create_user_credits(db, user_id)
        
        return CreditBalanceResponse(
            user_id=user_id,
            credits=user_credits.credits,
            plan_status=user_credits.plan_status,
            remaining_pro_days=user_credits.get_remaining_pro_days(),
            is_pro_active=user_credits.is_pro_active(),
            low_credit_warning=user_credits.credits <= CreditService.LOW_CREDIT_WARNING_THRESHOLD,
            can_perform_actions=user_credits.can_perform_action()
        )
    
    @staticmethod
    async def add_credits_for_activity(
        db: AsyncSession,
        user_id: int,
        event_type: CreditEventType,
        description: str = None,
        related_entity_type: str = None,
        related_entity_id: int = None,
        ip_address: str = None
    ) -> bool:
        """Fügt Credits für eine Benutzeraktivität hinzu"""
        
        # Prüfe ob es sich um eine Bauträger handelt
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user or user.user_role != UserRole.BAUTRAEGER:
            logger.warning(f"User {user_id} ist kein Bauträger, keine Credits hinzugefügt")
            return False
        
        # Hole UserCredits
        user_credits = await CreditService.get_or_create_user_credits(db, user_id)
        
        # Bestimme Credit-Belohnung
        credits_to_add = CreditService.CREDIT_REWARDS.get(event_type, 0)
        
        if credits_to_add <= 0:
            logger.warning(f"Keine Credits für Event-Typ {event_type}")
            return False
        
        # Füge Credits hinzu
        old_credits = user_credits.credits
        user_credits.credits += credits_to_add
        
        # Upgrade zu Pro falls nötig
        if user_credits.plan_status != PlanStatus.PRO and user_credits.credits > 0:
            user_credits.upgrade_to_pro()
            
            # Aktualisiere auch den subscription_plan in der User-Tabelle auf PRO
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    subscription_plan=SubscriptionPlan.PRO,
                    subscription_status=SubscriptionStatus.ACTIVE
                )
            )
        
        await db.commit()
        await db.refresh(user_credits)
        
        # Erstelle Credit-Event
        await CreditService.create_credit_event(
            db=db,
            user_credits_id=user_credits.id,
            event_type=event_type,
            credits_change=credits_to_add,
            description=description or f"Credits für {event_type.value}",
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            ip_address=ip_address
        )
        
        logger.info(f"User {user_id} hat {credits_to_add} Credits für {event_type.value} erhalten")
        return True
    
    @staticmethod
    async def process_daily_credit_deduction(
        db: AsyncSession,
        user_id: int
    ) -> bool:
        """Verarbeitet täglichen Credit-Abzug für Pro-Status"""
        
        user_credits = await CreditService.get_or_create_user_credits(db, user_id)
        
        # Prüfe ob User im Pro-Status ist
        if not user_credits.is_pro_active():
            return False
        
        # Ziehe täglichen Credit ab
        old_credits = user_credits.credits
        user_credits.credits -= CreditService.DAILY_CREDIT_DEDUCTION
        user_credits.total_pro_days += 1
        
        # Prüfe ob Credits aufgebraucht sind
        if user_credits.credits <= 0:
            user_credits.downgrade_to_basic()
            user_credits.credits = 0  # Nicht unter 0
            
            # Aktualisiere auch den subscription_plan in der User-Tabelle auf BASIC
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    subscription_plan=SubscriptionPlan.BASIC,
                    subscription_status=SubscriptionStatus.ACTIVE
                )
            )
            
            logger.info(f"User {user_id} wurde automatisch auf Basic downgraded")
        
        await db.commit()
        await db.refresh(user_credits)
        
        # Erstelle Credit-Event
        await CreditService.create_credit_event(
            db=db,
            user_credits_id=user_credits.id,
            event_type=CreditEventType.DAILY_DEDUCTION,
            credits_change=-CreditService.DAILY_CREDIT_DEDUCTION,
            description="Täglicher Pro-Status Abzug",
            ip_address=None
        )
        
        # Audit-Log
        await SecurityService.create_audit_log(
            db, user_id, AuditAction.DATA_UPDATE,
            f"Täglicher Credit-Abzug: {old_credits} -> {user_credits.credits}",
            resource_type="user_credits", resource_id=user_credits.id
        )
        
        return True
    
    @staticmethod
    async def create_credit_event(
        db: AsyncSession,
        user_credits_id: int,
        event_type: CreditEventType,
        credits_change: int,
        description: str = None,
        related_entity_type: str = None,
        related_entity_id: int = None,
        ip_address: str = None,
        stripe_payment_intent_id: str = None,
        stripe_session_id: str = None
    ) -> CreditEvent:
        """Erstellt ein Credit-Event"""
        
        # Hole UserCredits für aktuelle Credit-Anzahl
        result = await db.execute(
            select(UserCredits).where(UserCredits.id == user_credits_id)
        )
        user_credits = result.scalar_one_or_none()
        
        if not user_credits:
            raise ValueError("UserCredits nicht gefunden")
        
        # Erstelle Credit-Event
        credit_event = CreditEvent(
            user_credits_id=user_credits_id,
            event_type=event_type,
            credits_change=credits_change,
            credits_before=user_credits.credits,
            credits_after=user_credits.credits + credits_change,
            description=description,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            ip_address=ip_address,
            stripe_payment_intent_id=stripe_payment_intent_id,
            stripe_session_id=stripe_session_id
        )
        
        db.add(credit_event)
        await db.commit()
        await db.refresh(credit_event)
        
        return credit_event
    
    @staticmethod
    async def get_credit_events(
        db: AsyncSession,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[CreditEvent]:
        """Holt Credit-Events für einen Benutzer"""
        
        user_credits = await CreditService.get_or_create_user_credits(db, user_id)
        
        result = await db.execute(
            select(CreditEvent)
            .where(CreditEvent.user_credits_id == user_credits.id)
            .order_by(CreditEvent.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        return result.scalars().all()
    
    @staticmethod
    async def get_credit_packages() -> List[Dict]:
        """Gibt verfügbare Credit-Packages zurück"""
        
        packages = []
        for package_type in CreditPackage:
            package_info = CreditPackage.get_package_info(package_type)
            packages.append({
                "package_type": package_type.value,
                "name": package_info["name"],
                "credits": package_info["credits"],
                "price": package_info["price"],
                "price_per_credit": package_info["price_per_credit"],
                "description": package_info["description"],
                "popular": package_type == CreditPackage.MEDIUM,
                "best_value": package_type == CreditPackage.LARGE
            })
        
        return packages
    
    @staticmethod
    async def reward_inspection_quote_acceptance(
        db: AsyncSession,
        user_id: int,
        quote_id: int,
        inspection_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Belohnt den Bauträger mit Credits für die Annahme eines Angebots nach Besichtigung.
        Dies ist der Kernmechanismus zur Förderung des vollständigen Besichtigungsprozesses.
        """
        try:
            user_credits = await CreditService.get_or_create_user_credits(db, user_id)
            
            # Prüfe ob bereits eine Belohnung für dieses Angebot vergeben wurde
            existing_event = await db.execute(
                select(CreditEvent).where(
                    and_(
                        CreditEvent.user_credits_id == user_credits.id,
                        CreditEvent.event_type == CreditEventType.INSPECTION_QUOTE_ACCEPTED,
                        CreditEvent.related_entity_type == "quote",
                        CreditEvent.related_entity_id == quote_id
                    )
                )
            )
            
            if existing_event.scalar_one_or_none():
                logger.warning(f"Credit-Belohnung für Quote {quote_id} bereits vergeben")
                return False
            
            # Vergebe Credits
            credit_reward = CreditService.CREDIT_REWARDS[CreditEventType.INSPECTION_QUOTE_ACCEPTED]
            old_credits = user_credits.credits
            user_credits.credits += credit_reward
            
            # Reaktiviere Pro-Status falls deaktiviert
            if user_credits.plan_status != PlanStatus.PRO and user_credits.credits > 0:
                user_credits.plan_status = PlanStatus.PRO
                user_credits.pro_start_date = datetime.utcnow()
                logger.info(f"Pro-Status für User {user_id} durch Credit-Belohnung reaktiviert")
            
            # Erstelle Credit-Event
            description = f"Bonus für Annahme eines Angebots nach Besichtigung (Quote #{quote_id}"
            if inspection_id:
                description += f", Besichtigung #{inspection_id}"
            description += ")"
            
            await CreditService.create_credit_event(
                db=db,
                user_credits_id=user_credits.id,
                event_type=CreditEventType.INSPECTION_QUOTE_ACCEPTED,
                credits_change=credit_reward,
                description=description,
                related_entity_type="quote",
                related_entity_id=quote_id,
                ip_address=ip_address
            )
            
            # Audit-Log
            await SecurityService.create_audit_log(
                db, user_id, AuditAction.DATA_UPDATE,
                f"Credit-Belohnung für Besichtigungsangebot: {old_credits} -> {user_credits.credits} (+{credit_reward})",
                resource_type="user_credits", resource_id=user_credits.id
            )
            
            logger.info(f"Credit-Belohnung vergeben: User {user_id}, Quote {quote_id}, +{credit_reward} Credits")
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei Credit-Belohnung: {str(e)}")
            await db.rollback()
            return False
    
    @staticmethod
    async def create_credit_purchase(
        db: AsyncSession,
        user_id: int,
        package_type: CreditPackage,
        stripe_session_id: str,
        user_email: str,
        ip_address: str = None
    ) -> CreditPurchase:
        """Erstellt einen Credit-Kauf"""
        
        user_credits = await CreditService.get_or_create_user_credits(db, user_id)
        package_info = package_type.get_package_info()
        
        purchase = CreditPurchase(
            user_credits_id=user_credits.id,
            package_type=package_type,
            credits_amount=package_info["credits"],
            price_chf=package_info["price"],
            stripe_session_id=stripe_session_id,
            user_email=user_email,
            user_ip_address=ip_address
        )
        
        db.add(purchase)
        await db.commit()
        await db.refresh(purchase)
        
        return purchase
    
    @staticmethod
    async def complete_credit_purchase(
        db: AsyncSession,
        stripe_session_id: str,
        stripe_payment_intent_id: str = None
    ) -> bool:
        """Vervollständigt einen Credit-Kauf nach Stripe-Webhook"""
        
        # Finde Purchase
        result = await db.execute(
            select(CreditPurchase).where(CreditPurchase.stripe_session_id == stripe_session_id)
        )
        purchase = result.scalar_one_or_none()
        
        if not purchase:
            logger.error(f"Credit-Purchase mit Session ID {stripe_session_id} nicht gefunden")
            return False
        
        # Aktualisiere Purchase-Status
        purchase.status = PurchaseStatus.COMPLETED
        purchase.stripe_payment_intent_id = stripe_payment_intent_id
        purchase.completed_at = datetime.now()
        
        # Füge Credits zum User hinzu
        user_credits = purchase.user_credits
        old_credits = user_credits.credits
        user_credits.credits += purchase.credits_amount
        
        # Upgrade zu Pro falls nötig
        if user_credits.plan_status != PlanStatus.PRO and user_credits.credits > 0:
            user_credits.upgrade_to_pro()
        
        await db.commit()
        await db.refresh(purchase)
        await db.refresh(user_credits)
        
        # Erstelle Credit-Event
        await CreditService.create_credit_event(
            db=db,
            user_credits_id=user_credits.id,
            event_type=CreditEventType.PURCHASE_CREDITS,
            credits_change=purchase.credits_amount,
            description=f"Credits gekauft: {purchase.get_package_info()['name']}",
            stripe_payment_intent_id=stripe_payment_intent_id,
            stripe_session_id=stripe_session_id,
            ip_address=purchase.user_ip_address
        )
        
        logger.info(f"Credit-Purchase für User {user_credits.user_id} abgeschlossen: {purchase.credits_amount} Credits")
        return True
    
    @staticmethod
    async def manual_credit_adjustment(
        db: AsyncSession,
        adjustment_request: CreditAdjustmentRequest,
        admin_user_id: int
    ) -> bool:
        """Manuelle Credit-Anpassung durch Admin"""
        
        user_credits = await CreditService.get_or_create_user_credits(db, adjustment_request.user_id)
        
        old_credits = user_credits.credits
        user_credits.credits += adjustment_request.credits_change
        
        # Stelle sicher, dass Credits nicht unter 0 fallen
        if user_credits.credits < 0:
            user_credits.credits = 0
        
        # Upgrade/Downgrade basierend auf Credits
        if user_credits.credits > 0:
            user_credits.upgrade_to_pro()
            # Aktualisiere auch den subscription_plan in der User-Tabelle auf PRO
            await db.execute(
                update(User)
                .where(User.id == adjustment_request.user_id)
                .values(
                    subscription_plan=SubscriptionPlan.PRO,
                    subscription_status=SubscriptionStatus.ACTIVE
                )
            )
        else:
            user_credits.downgrade_to_basic()
            # Aktualisiere auch den subscription_plan in der User-Tabelle auf BASIC
            await db.execute(
                update(User)
                .where(User.id == adjustment_request.user_id)
                .values(
                    subscription_plan=SubscriptionPlan.BASIC,
                    subscription_status=SubscriptionStatus.ACTIVE
                )
            )
        
        await db.commit()
        await db.refresh(user_credits)
        
        # Erstelle Credit-Event
        event_type = CreditEventType.MANUAL_ADJUSTMENT
        await CreditService.create_credit_event(
            db=db,
            user_credits_id=user_credits.id,
            event_type=event_type,
            credits_change=adjustment_request.credits_change,
            description=f"Manuelle Anpassung: {adjustment_request.reason}",
            ip_address=None
        )
        
        # Audit-Log
        await SecurityService.create_audit_log(
            db, admin_user_id, AuditAction.DATA_UPDATE,
            f"Manuelle Credit-Anpassung für User {adjustment_request.user_id}: {old_credits} -> {user_credits.credits}",
            resource_type="user_credits", resource_id=user_credits.id
        )
        
        logger.info(f"Admin {admin_user_id} hat Credits für User {adjustment_request.user_id} angepasst: {adjustment_request.credits_change}")
        return True
    
    @staticmethod
    async def initialize_credits_for_new_user(
        db: AsyncSession,
        user_id: int,
        user_role: UserRole,
        ip_address: str = None
    ) -> bool:
        """Initialisiert Credits für einen neuen Benutzer bei Onboarding"""
        
        # Nur Bauträger erhalten Credits
        if user_role != UserRole.BAUTRAEGER:
            logger.info(f"User {user_id} ist kein Bauträger, keine Credits initialisiert")
            return False
        
        # Prüfe ob bereits UserCredits existiert
        result = await db.execute(
            select(UserCredits).where(UserCredits.user_id == user_id)
        )
        existing_credits = result.scalar_one_or_none()
        
        if existing_credits:
            logger.info(f"UserCredits für User {user_id} bereits existiert")
            return True
        
        # Erstelle UserCredits mit Start-Credits (90 Credits Willkommensbonus)
        user_credits = UserCredits(
            user_id=user_id,
            credits=90,  # Willkommensbonus: 90 Credits
            plan_status=PlanStatus.PRO,
            pro_start_date=datetime.now()
        )
        
        db.add(user_credits)
        await db.flush()
        
        # Aktualisiere auch den subscription_plan in der User-Tabelle auf PRO
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                subscription_plan=SubscriptionPlan.PRO,
                subscription_status='ACTIVE'
            )
        )
        
        await db.commit()
        await db.refresh(user_credits)
        
        # Erstelle Registrierungs-Bonus Event
        await CreditService.create_credit_event(
            db=db,
            user_credits_id=user_credits.id,
            event_type=CreditEventType.REGISTRATION_BONUS,
            credits_change=90,
            description="🎉 Willkommensbonus! 90 Credits für Ihren Start mit BuildWise Pro",
            ip_address=ip_address
        )
        
        # Audit-Log
        await SecurityService.create_audit_log(
            db, user_id, AuditAction.DATA_CREATE,
            f"Credits für neuen Bauträger initialisiert: 90 Credits Willkommensbonus",
            resource_type="user_credits", resource_id=user_credits.id,
            ip_address=ip_address
        )
        
        logger.info(f"Credits für neuen Bauträger {user_id} initialisiert: 90 Credits Willkommensbonus")
        return True
    
    @staticmethod
    async def process_all_daily_deductions(db: AsyncSession) -> Dict[str, int]:
        """Verarbeitet tägliche Credit-Abzüge für alle aktiven Pro-User"""
        
        # Hole alle aktiven Pro-User
        result = await db.execute(
            select(UserCredits)
            .where(UserCredits.plan_status == PlanStatus.PRO)
            .where(UserCredits.credits > 0)
        )
        active_pro_users = result.scalars().all()
        
        processed_count = 0
        downgraded_count = 0
        
        for user_credits in active_pro_users:
            try:
                # Verarbeite täglichen Abzug
                old_credits = user_credits.credits
                user_credits.credits -= CreditService.DAILY_CREDIT_DEDUCTION
                user_credits.total_pro_days += 1
                
                # Prüfe ob Credits aufgebraucht sind
                if user_credits.credits <= 0:
                    user_credits.downgrade_to_basic()
                    user_credits.credits = 0
                    
                    # Aktualisiere auch den subscription_plan in der User-Tabelle auf BASIC
                    await db.execute(
                        update(User)
                        .where(User.id == user_credits.user_id)
                        .values(
                            subscription_plan=SubscriptionPlan.BASIC,
                            subscription_status='ACTIVE'
                        )
                    )
                    
                    downgraded_count += 1
                
                # Erstelle Credit-Event
                await CreditService.create_credit_event(
                    db=db,
                    user_credits_id=user_credits.id,
                    event_type=CreditEventType.DAILY_DEDUCTION,
                    credits_change=-CreditService.DAILY_CREDIT_DEDUCTION,
                    description="Täglicher Pro-Status Abzug",
                    ip_address=None
                )
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Fehler bei täglichem Credit-Abzug für User {user_credits.user_id}: {e}")
                continue
        
        await db.commit()
        
        logger.info(f"Tägliche Credit-Abzüge verarbeitet: {processed_count} User, {downgraded_count} downgraded")
        
        return {
            "processed_users": processed_count,
            "downgraded_users": downgraded_count
        } 