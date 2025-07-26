from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

from ..models.user_credits import PlanStatus


class UserCreditsBase(BaseModel):
    credits: int = Field(..., ge=0, description="Aktuelle Anzahl Credits")
    plan_status: PlanStatus = Field(..., description="Aktueller Plan-Status")
    auto_downgrade_enabled: bool = Field(default=True, description="Automatischer Downgrade aktiviert")


class UserCreditsCreate(UserCreditsBase):
    user_id: int = Field(..., gt=0, description="User ID")


class UserCreditsUpdate(BaseModel):
    credits: Optional[int] = Field(None, ge=0, description="Neue Anzahl Credits")
    plan_status: Optional[PlanStatus] = Field(None, description="Neuer Plan-Status")
    auto_downgrade_enabled: Optional[bool] = Field(None, description="Automatischer Downgrade")


class UserCreditsRead(UserCreditsBase):
    id: int
    user_id: int
    pro_start_date: Optional[datetime] = None
    last_pro_day: Optional[datetime] = None
    total_pro_days: int = Field(default=0, description="Gesamte Pro-Tage")
    low_credit_warning_sent: bool = Field(default=False, description="Niedrige Credits Warnung gesendet")
    downgrade_notification_sent: bool = Field(default=False, description="Downgrade Benachrichtigung gesendet")
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CreditBalanceResponse(BaseModel):
    """Response für Credit-Balance Abfragen"""
    user_id: int
    credits: int
    plan_status: PlanStatus
    remaining_pro_days: int = Field(..., description="Verbleibende Pro-Tage")
    is_pro_active: bool = Field(..., description="Ist Pro-Status aktiv")
    low_credit_warning: bool = Field(default=False, description="Niedrige Credits Warnung")
    can_perform_actions: bool = Field(..., description="Kann Aktionen durchführen")
    
    class Config:
        from_attributes = True


class CreditEventBase(BaseModel):
    event_type: str = Field(..., description="Typ des Credit-Events")
    credits_change: int = Field(..., description="Änderung der Credits")
    description: Optional[str] = Field(None, description="Beschreibung des Events")
    related_entity_type: Optional[str] = Field(None, description="Typ der verknüpften Entität")
    related_entity_id: Optional[int] = Field(None, description="ID der verknüpften Entität")


class CreditEventCreate(CreditEventBase):
    user_credits_id: int = Field(..., gt=0, description="UserCredits ID")


class CreditEventRead(CreditEventBase):
    id: int
    user_credits_id: int
    credits_before: int
    credits_after: int
    stripe_payment_intent_id: Optional[str] = None
    stripe_session_id: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class CreditPurchaseBase(BaseModel):
    package_type: str = Field(..., description="Typ des Credit-Packages")
    credits_amount: int = Field(..., gt=0, description="Anzahl Credits im Package")
    price_chf: float = Field(..., gt=0, description="Preis in CHF")


class CreditPurchaseCreate(CreditPurchaseBase):
    user_credits_id: int = Field(..., gt=0, description="UserCredits ID")
    user_email: str = Field(..., description="E-Mail des Benutzers")
    stripe_session_id: str = Field(..., description="Stripe Session ID")


class CreditPurchaseRead(CreditPurchaseBase):
    id: int
    user_credits_id: int
    status: str = Field(..., description="Status des Kaufs")
    stripe_session_id: str
    stripe_payment_intent_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    purchased_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    user_email: str
    user_ip_address: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CreditPackageInfo(BaseModel):
    """Informationen über verfügbare Credit-Packages"""
    package_type: str
    name: str
    credits: int
    price: float
    price_per_credit: float
    description: str
    popular: bool = Field(default=False, description="Beliebtes Package")
    best_value: bool = Field(default=False, description="Bester Wert")


class CreditSystemStatus(BaseModel):
    """Gesamtstatus des Credit-Systems"""
    user_id: int
    credits: int
    plan_status: PlanStatus
    remaining_pro_days: int
    is_pro_active: bool
    can_perform_actions: bool
    low_credit_warning: bool
    downgrade_notification: bool
    available_packages: List[CreditPackageInfo]
    recent_events: List[CreditEventRead]
    total_events: int
    total_purchases: int
    total_spent_chf: float


class CreditAdjustmentRequest(BaseModel):
    """Request für manuelle Credit-Anpassungen (Admin)"""
    user_id: int = Field(..., gt=0, description="User ID")
    credits_change: int = Field(..., description="Änderung der Credits (positiv oder negativ)")
    reason: str = Field(..., min_length=1, max_length=500, description="Grund für die Anpassung")
    admin_note: Optional[str] = Field(None, max_length=1000, description="Admin-Notiz")


class CreditEventFilter(BaseModel):
    """Filter für Credit-Events"""
    event_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=50, le=100, description="Maximale Anzahl Events")
    offset: int = Field(default=0, ge=0, description="Offset für Pagination") 