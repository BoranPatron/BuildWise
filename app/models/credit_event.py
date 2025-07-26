from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Float, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .base import Base


class CreditEventType(enum.Enum):
    # Automatische Events
    DAILY_DEDUCTION = "daily_deduction"
    AUTO_DOWNGRADE = "auto_downgrade"
    PRO_UPGRADE = "pro_upgrade"
    
    # User-Aktivitäten (Credits verdienen)
    QUOTE_ACCEPTED = "quote_accepted"  # +5 Credits
    INSPECTION_QUOTE_ACCEPTED = "inspection_quote_accepted"  # +15 Credits (Bonus für Besichtigungsprozess!)
    INVOICE_RECEIVED = "invoice_received"  # +3 Credits
    PROJECT_COMPLETED = "project_completed"  # +10 Credits
    PROVIDER_REVIEW = "provider_review"  # +2 Credits
    MILESTONE_COMPLETED = "milestone_completed"  # +3 Credits
    DOCUMENT_UPLOADED = "document_uploaded"  # +1 Credit
    EXPENSE_ADDED = "expense_added"  # +1 Credit
    
    # Manuelle Events
    MANUAL_ADJUSTMENT = "manual_adjustment"
    PURCHASE_CREDITS = "purchase_credits"
    REFUND_CREDITS = "refund_credits"
    BONUS_CREDITS = "bonus_credits"
    
    # System Events
    REGISTRATION_BONUS = "registration_bonus"  # +100 Credits
    REFERRAL_BONUS = "referral_bonus"  # +20 Credits
    LOYALTY_BONUS = "loyalty_bonus"  # +10 Credits


class CreditEvent(Base):
    __tablename__ = "credit_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_credits_id = Column(Integer, ForeignKey("user_credits.id", ondelete="CASCADE"), nullable=False)
    
    # Event-Details
    event_type = Column(Enum(CreditEventType), nullable=False)
    credits_change = Column(Integer, nullable=False)  # Positive für Hinzufügung, negative für Abzug
    credits_before = Column(Integer, nullable=False)
    credits_after = Column(Integer, nullable=False)
    
    # Kontext-Informationen
    description = Column(Text, nullable=True)
    related_entity_type = Column(String(50), nullable=True)  # "quote", "project", "invoice", etc.
    related_entity_id = Column(Integer, nullable=True)
    
    # Stripe-Integration (für Käufe)
    stripe_payment_intent_id = Column(String(255), nullable=True)
    stripe_session_id = Column(String(255), nullable=True)
    
    # IP-Adresse für Sicherheit
    ip_address = Column(String(45), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user_credits = relationship("UserCredits", back_populates="credit_events")
    
    def get_event_description(self) -> str:
        """Gibt eine benutzerfreundliche Beschreibung des Events zurück"""
        descriptions = {
            CreditEventType.DAILY_DEDUCTION: "Täglicher Pro-Status Abzug",
            CreditEventType.AUTO_DOWNGRADE: "Automatischer Downgrade auf Basic",
            CreditEventType.PRO_UPGRADE: "Upgrade auf Pro-Status",
            CreditEventType.QUOTE_ACCEPTED: "Angebot angenommen",
            CreditEventType.INSPECTION_QUOTE_ACCEPTED: "Angebot nach Besichtigung angenommen (Bonus!)",
            CreditEventType.INVOICE_RECEIVED: "Rechnung erhalten",
            CreditEventType.PROJECT_COMPLETED: "Projekt abgeschlossen",
            CreditEventType.PROVIDER_REVIEW: "Dienstleister bewertet",
            CreditEventType.MILESTONE_COMPLETED: "Meilenstein abgeschlossen",
            CreditEventType.DOCUMENT_UPLOADED: "Dokument hochgeladen",
            CreditEventType.EXPENSE_ADDED: "Ausgabe hinzugefügt",
            CreditEventType.MANUAL_ADJUSTMENT: "Manuelle Anpassung",
            CreditEventType.PURCHASE_CREDITS: "Credits gekauft",
            CreditEventType.REFUND_CREDITS: "Credits erstattet",
            CreditEventType.BONUS_CREDITS: "Bonus-Credits erhalten",
            CreditEventType.REGISTRATION_BONUS: "Registrierungs-Bonus",
            CreditEventType.REFERRAL_BONUS: "Empfehlungs-Bonus",
            CreditEventType.LOYALTY_BONUS: "Treue-Bonus"
        }
        return descriptions.get(self.event_type, str(self.event_type.value))
    
    def is_positive_event(self) -> bool:
        """Prüft ob es sich um ein positives Event handelt (Credits hinzugefügt)"""
        return self.credits_change > 0
    
    def is_negative_event(self) -> bool:
        """Prüft ob es sich um ein negatives Event handelt (Credits abgezogen)"""
        return self.credits_change < 0
    
    def get_formatted_credits_change(self) -> str:
        """Gibt die Credit-Änderung formatiert zurück"""
        if self.credits_change > 0:
            return f"+{self.credits_change}"
        return str(self.credits_change) 