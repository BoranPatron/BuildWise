from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Float, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .base import Base


class PlanStatus(enum.Enum):
    PRO = "pro"
    BASIC = "basic"
    EXPIRED = "expired"


class UserCredits(Base):
    __tablename__ = "user_credits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Credit-Management
    credits = Column(Integer, default=100, nullable=False)  # Start-Credits: 100
    plan_status = Column(Enum(PlanStatus), default=PlanStatus.PRO, nullable=False)
    
    # Pro-Status Tracking
    pro_start_date = Column(DateTime(timezone=True), server_default=func.now())
    last_pro_day = Column(DateTime(timezone=True), nullable=True)  # Letzter Tag im Pro-Status
    total_pro_days = Column(Integer, default=0)  # Gesamte Pro-Tage
    
    # Automatische Downgrade-Einstellungen
    auto_downgrade_enabled = Column(Boolean, default=True)
    low_credit_warning_sent = Column(Boolean, default=False)
    downgrade_notification_sent = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_credits")
    credit_events = relationship("CreditEvent", back_populates="user_credits", cascade="all, delete-orphan")
    credit_purchases = relationship("CreditPurchase", back_populates="user_credits", cascade="all, delete-orphan")
    
    def is_pro_active(self) -> bool:
        """Prüft ob der Pro-Status aktiv ist"""
        return self.plan_status == PlanStatus.PRO and self.credits > 0
    
    def get_remaining_pro_days(self) -> int:
        """Berechnet die verbleibenden Pro-Tage basierend auf Credits"""
        return max(0, self.credits)
    
    def can_perform_action(self, required_credits: int = 0) -> bool:
        """Prüft ob eine Aktion mit den verfügbaren Credits durchgeführt werden kann"""
        if self.plan_status == PlanStatus.PRO:
            return self.credits >= required_credits
        return False
    
    def add_credits(self, amount: int, reason: str = "Manual") -> bool:
        """Fügt Credits hinzu"""
        if amount > 0:
            self.credits += amount
            return True
        return False
    
    def deduct_credits(self, amount: int, reason: str = "Daily") -> bool:
        """Zieht Credits ab"""
        if amount > 0 and self.credits >= amount:
            self.credits -= amount
            return True
        return False
    
    def upgrade_to_pro(self) -> bool:
        """Upgraded den Benutzer auf Pro-Status"""
        if self.credits > 0:
            self.plan_status = PlanStatus.PRO
            self.pro_start_date = func.now()
            return True
        return False
    
    def downgrade_to_basic(self) -> bool:
        """Downgraded den Benutzer auf Basic-Status"""
        self.plan_status = PlanStatus.BASIC
        self.last_pro_day = func.now()
        return True 