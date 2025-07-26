from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Float, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .base import Base


class PurchaseStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class CreditPackage(enum.Enum):
    SMALL = "small"      # 30 Credits für 10 CHF
    MEDIUM = "medium"    # 100 Credits für 30 CHF
    LARGE = "large"      # 300 Credits für 80 CHF
    XLARGE = "xlarge"    # 1000 Credits für 200 CHF
    
    @classmethod
    def get_package_info(cls, package_type=None) -> dict:
        """Gibt Informationen über Credit-Packages zurück"""
        package_info = {
            cls.SMALL: {
                "name": "Kleines Paket",
                "credits": 30,
                "price": 10.0,
                "price_per_credit": 0.33,
                "description": "Perfekt für den Start"
            },
            cls.MEDIUM: {
                "name": "Mittleres Paket",
                "credits": 100,
                "price": 30.0,
                "price_per_credit": 0.30,
                "description": "Beliebt bei aktiven Nutzern"
            },
            cls.LARGE: {
                "name": "Großes Paket",
                "credits": 300,
                "price": 80.0,
                "price_per_credit": 0.27,
                "description": "Beste Wert für Profis"
            },
            cls.XLARGE: {
                "name": "XXL Paket",
                "credits": 1000,
                "price": 200.0,
                "price_per_credit": 0.20,
                "description": "Maximaler Rabatt"
            }
        }
        
        if package_type:
            return package_info.get(package_type, {})
        return package_info


class CreditPurchase(Base):
    __tablename__ = "credit_purchases"
    
    id = Column(Integer, primary_key=True, index=True)
    user_credits_id = Column(Integer, ForeignKey("user_credits.id", ondelete="CASCADE"), nullable=False)
    
    # Package-Details
    package_type = Column(Enum(CreditPackage), nullable=False)
    credits_amount = Column(Integer, nullable=False)
    price_chf = Column(Float, nullable=False)
    
    # Stripe-Integration
    stripe_session_id = Column(String(255), nullable=False, unique=True)
    stripe_payment_intent_id = Column(String(255), nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    
    # Status und Tracking
    status = Column(Enum(PurchaseStatus), default=PurchaseStatus.PENDING, nullable=False)
    purchased_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Benutzer-Informationen
    user_email = Column(String(255), nullable=False)
    user_ip_address = Column(String(45), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user_credits = relationship("UserCredits", back_populates="credit_purchases")
    
    def get_package_info(self) -> dict:
        """Gibt Informationen über das Credit-Package zurück"""
        package_info = {
            CreditPackage.SMALL: {
                "name": "Kleines Paket",
                "credits": 30,
                "price": 10.0,
                "price_per_credit": 0.33,
                "description": "Perfekt für den Start"
            },
            CreditPackage.MEDIUM: {
                "name": "Mittleres Paket",
                "credits": 100,
                "price": 30.0,
                "price_per_credit": 0.30,
                "description": "Beliebt bei aktiven Nutzern"
            },
            CreditPackage.LARGE: {
                "name": "Großes Paket",
                "credits": 300,
                "price": 80.0,
                "price_per_credit": 0.27,
                "description": "Beste Wert für Profis"
            },
            CreditPackage.XLARGE: {
                "name": "XXL Paket",
                "credits": 1000,
                "price": 200.0,
                "price_per_credit": 0.20,
                "description": "Maximaler Rabatt"
            }
        }
        return package_info.get(self.package_type, {})
    
    def is_completed(self) -> bool:
        """Prüft ob der Kauf abgeschlossen ist"""
        return self.status == PurchaseStatus.COMPLETED
    
    def is_pending(self) -> bool:
        """Prüft ob der Kauf ausstehend ist"""
        return self.status == PurchaseStatus.PENDING
    
    def can_be_refunded(self) -> bool:
        """Prüft ob der Kauf erstattet werden kann"""
        return self.status == PurchaseStatus.COMPLETED
    
    def get_formatted_price(self) -> str:
        """Gibt den Preis formatiert zurück"""
        return f"{self.price_chf:.2f} CHF"
    
    def get_price_per_credit(self) -> float:
        """Berechnet den Preis pro Credit"""
        if self.credits_amount > 0:
            return self.price_chf / self.credits_amount
        return 0.0 