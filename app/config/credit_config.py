"""
BuildWise Credit Configuration

Dieses Modul enthält die zentrale Konfiguration für das Credit-System.
Hier können alle Credit-Belohnungen und -Abzüge für verschiedene Aktionen konfiguriert werden.

Änderungen an dieser Datei werden sofort wirksam, ohne dass der Code neu kompiliert werden muss.
"""

from typing import Dict, Any
from ..models.credit_event import CreditEventType


class CreditConfig:
    """
    Zentrale Konfiguration für das BuildWise Credit-System.
    
    Diese Klasse enthält alle konfigurierbaren Werte für Credit-Belohnungen,
    Abzüge und System-Parameter.
    """
    
    # =============================================================================
    # CREDIT-BELOHNUNGEN FÜR VERSCHIEDENE AKTIONEN
    # =============================================================================
    
    # Credit-Rewards für verschiedene Aktionen (können hier einfach angepasst werden)
    CREDIT_REWARDS: Dict[CreditEventType, int] = {
        # === USER-AKTIVITÄTEN (Credits verdienen) ===
        CreditEventType.QUOTE_ACCEPTED: 5,                    # Angebot angenommen
        CreditEventType.INSPECTION_QUOTE_ACCEPTED: 15,         # Angebot nach Besichtigung angenommen (Bonus!)
        CreditEventType.INVOICE_RECEIVED: 0,                   # Rechnung erhalten
        CreditEventType.PROJECT_COMPLETED: 10,                # Projekt abgeschlossen
        CreditEventType.PROVIDER_REVIEW: 2,                    # Dienstleister bewertet
        CreditEventType.MILESTONE_COMPLETED: 1,               # Meilenstein abgeschlossen
        CreditEventType.DOCUMENT_UPLOADED: 0,                 # Dokument hochgeladen
        CreditEventType.EXPENSE_ADDED: 0,                     # Ausgabe hinzugefügt
        
        # === SYSTEM-EVENTS (Bonuses) ===
        CreditEventType.REGISTRATION_BONUS: 90,                # Registrierungs-Bonus (Willkommensbonus)
        CreditEventType.REFERRAL_BONUS: 20,                   # Empfehlungs-Bonus
        CreditEventType.LOYALTY_BONUS: 10,                    # Treue-Bonus
        
        # === MANUELLE EVENTS ===
        CreditEventType.MANUAL_ADJUSTMENT: 0,                 # Manuelle Anpassung (wird dynamisch gesetzt)
        CreditEventType.PURCHASE_CREDITS: 0,                  # Credits gekauft (wird dynamisch gesetzt)
        CreditEventType.REFUND_CREDITS: 0,                    # Credits erstattet (wird dynamisch gesetzt)
        CreditEventType.BONUS_CREDITS: 0,                     # Bonus-Credits (wird dynamisch gesetzt)
        
        # === AUTOMATISCHE EVENTS ===
        CreditEventType.DAILY_DEDUCTION: 0,                    # Täglicher Abzug (wird als negativer Wert behandelt)
        CreditEventType.AUTO_DOWNGRADE: 0,                    # Automatischer Downgrade
        CreditEventType.PRO_UPGRADE: 0,                       # Pro-Upgrade
    }
    
    # =============================================================================
    # SYSTEM-PARAMETER
    # =============================================================================
    
    # Täglicher Credit-Abzug für Pro-Status
    DAILY_CREDIT_DEDUCTION: int = 1
    
    # Warnung bei niedrigen Credits
    LOW_CREDIT_WARNING_THRESHOLD: int = 10
    
    # Mindest-Credits für Pro-Status Aktivierung
    MIN_CREDITS_FOR_PRO: int = 1
    
    # =============================================================================
    # BONUS-KONFIGURATION
    # =============================================================================
    
    # Besichtigungs-Bonus Multiplikator (zusätzlich zu normalen Quote-Accepted Credits)
    INSPECTION_BONUS_MULTIPLIER: float = 3.0  # 5 Credits * 3.0 = 15 Credits total
    
    # Treue-Bonus Konfiguration
    LOYALTY_BONUS_TRIGGER_DAYS: int = 30       # Nach wie vielen Tagen Pro-Status
    LOYALTY_BONUS_AMOUNT: int = 10             # Wie viele Credits als Treue-Bonus
    
    # Empfehlungs-Bonus Konfiguration
    REFERRAL_BONUS_AMOUNT: int = 20            # Credits für erfolgreiche Empfehlung
    
    # =============================================================================
    # CREDIT-PACKAGE KONFIGURATION
    # =============================================================================
    
    # Verfügbare Credit-Packages (können hier angepasst werden)
    CREDIT_PACKAGES: Dict[str, Dict[str, Any]] = {
        "small": {
            "name": "Starter Package",
            "credits": 50,
            "price_chf": 25.00,
            "description": "Perfekt für den Einstieg",
            "popular": False,
            "best_value": False
        },
        "medium": {
            "name": "Professional Package",
            "credits": 150,
            "price_chf": 60.00,
            "description": "Ideal für aktive Bauträger",
            "popular": True,
            "best_value": False
        },
        "large": {
            "name": "Enterprise Package",
            "credits": 500,
            "price_chf": 180.00,
            "description": "Maximale Flexibilität",
            "popular": False,
            "best_value": True
        }
    }
    
    # =============================================================================
    # FEATURE-FLAGS UND ERWEITERTE KONFIGURATION
    # =============================================================================
    
    # Feature-Flags für verschiedene Credit-Features
    FEATURE_FLAGS: Dict[str, bool] = {
        "enable_inspection_bonus": True,        # Besichtigungs-Bonus aktiviert
        "enable_loyalty_bonus": True,          # Treue-Bonus aktiviert
        "enable_referral_bonus": True,         # Empfehlungs-Bonus aktiviert
        "enable_daily_deduction": True,        # Täglicher Abzug aktiviert
        "enable_auto_upgrade": True,           # Automatisches Upgrade aktiviert
        "enable_auto_downgrade": True,         # Automatisches Downgrade aktiviert
    }
    
    # Maximale Credits pro Tag (Anti-Spam Schutz)
    MAX_CREDITS_PER_DAY: int = 100
    
    # Maximale Credits pro Aktion pro Tag
    MAX_CREDITS_PER_ACTION_PER_DAY: Dict[CreditEventType, int] = {
        CreditEventType.QUOTE_ACCEPTED: 50,
        CreditEventType.INSPECTION_QUOTE_ACCEPTED: 50,
        CreditEventType.INVOICE_RECEIVED: 30,
        CreditEventType.PROJECT_COMPLETED: 20,
        CreditEventType.PROVIDER_REVIEW: 20,
        CreditEventType.MILESTONE_COMPLETED: 30,
        CreditEventType.DOCUMENT_UPLOADED: 10,
        CreditEventType.EXPENSE_ADDED: 10,
    }
    
    # =============================================================================
    # HELPER-METHODEN
    # =============================================================================
    
    @classmethod
    def get_credit_reward(cls, event_type: CreditEventType) -> int:
        """
        Holt die Credit-Belohnung für einen bestimmten Event-Typ.
        
        Args:
            event_type: Der Event-Typ für den die Belohnung abgerufen werden soll
            
        Returns:
            Anzahl der Credits die vergeben werden sollen
        """
        return cls.CREDIT_REWARDS.get(event_type, 0)
    
    @classmethod
    def is_feature_enabled(cls, feature_name: str) -> bool:
        """
        Prüft ob ein bestimmtes Feature aktiviert ist.
        
        Args:
            feature_name: Name des Features das geprüft werden soll
            
        Returns:
            True wenn das Feature aktiviert ist, False sonst
        """
        return cls.FEATURE_FLAGS.get(feature_name, False)
    
    @classmethod
    def get_max_credits_per_action_per_day(cls, event_type: CreditEventType) -> int:
        """
        Holt das Maximum an Credits die pro Tag für eine bestimmte Aktion vergeben werden können.
        
        Args:
            event_type: Der Event-Typ für den das Maximum abgerufen werden soll
            
        Returns:
            Maximale Anzahl Credits pro Tag für diese Aktion
        """
        return cls.MAX_CREDITS_PER_ACTION_PER_DAY.get(event_type, 0)
    
    @classmethod
    def update_credit_reward(cls, event_type: CreditEventType, new_amount: int) -> None:
        """
        Aktualisiert die Credit-Belohnung für einen bestimmten Event-Typ.
        
        Args:
            event_type: Der Event-Typ dessen Belohnung aktualisiert werden soll
            new_amount: Neue Anzahl der Credits
        """
        cls.CREDIT_REWARDS[event_type] = new_amount
    
    @classmethod
    def toggle_feature(cls, feature_name: str, enabled: bool = None) -> bool:
        """
        Aktiviert oder deaktiviert ein Feature.
        
        Args:
            feature_name: Name des Features
            enabled: True um zu aktivieren, False um zu deaktivieren, None um zu togglen
            
        Returns:
            Neuer Status des Features
        """
        if enabled is None:
            # Toggle current state
            cls.FEATURE_FLAGS[feature_name] = not cls.FEATURE_FLAGS.get(feature_name, False)
        else:
            cls.FEATURE_FLAGS[feature_name] = enabled
        
        return cls.FEATURE_FLAGS[feature_name]
    
    @classmethod
    def get_all_config(cls) -> Dict[str, Any]:
        """
        Gibt die komplette Konfiguration als Dictionary zurück.
        
        Returns:
            Dictionary mit allen Konfigurationswerten
        """
        return {
            "credit_rewards": {event_type.value: amount for event_type, amount in cls.CREDIT_REWARDS.items()},
            "daily_credit_deduction": cls.DAILY_CREDIT_DEDUCTION,
            "low_credit_warning_threshold": cls.LOW_CREDIT_WARNING_THRESHOLD,
            "min_credits_for_pro": cls.MIN_CREDITS_FOR_PRO,
            "inspection_bonus_multiplier": cls.INSPECTION_BONUS_MULTIPLIER,
            "loyalty_bonus_trigger_days": cls.LOYALTY_BONUS_TRIGGER_DAYS,
            "loyalty_bonus_amount": cls.LOYALTY_BONUS_AMOUNT,
            "referral_bonus_amount": cls.REFERRAL_BONUS_AMOUNT,
            "credit_packages": cls.CREDIT_PACKAGES,
            "feature_flags": cls.FEATURE_FLAGS,
            "max_credits_per_day": cls.MAX_CREDITS_PER_DAY,
            "max_credits_per_action_per_day": {event_type.value: amount for event_type, amount in cls.MAX_CREDITS_PER_ACTION_PER_DAY.items()}
        }


# =============================================================================
# GLOBALE INSTANZ FÜR EINFACHE VERWENDUNG
# =============================================================================

# Globale Instanz der Credit-Konfiguration
credit_config = CreditConfig()


# =============================================================================
# KONFIGURATIONS-VALIDIERUNG
# =============================================================================

def validate_credit_config() -> bool:
    """
    Validiert die Credit-Konfiguration auf Konsistenz.
    
    Returns:
        True wenn die Konfiguration gültig ist, False sonst
    """
    try:
        # Prüfe ob alle CreditEventType Werte in CREDIT_REWARDS vorhanden sind
        for event_type in CreditEventType:
            if event_type not in credit_config.CREDIT_REWARDS:
                print(f"WARNUNG: {event_type.value} nicht in CREDIT_REWARDS definiert")
        
        # Prüfe ob alle Werte nicht-negativ sind (außer für Abzüge)
        for event_type, amount in credit_config.CREDIT_REWARDS.items():
            if amount < 0 and event_type not in [CreditEventType.DAILY_DEDUCTION]:
                print(f"WARNUNG: Negative Credits für {event_type.value}: {amount}")
        
        # Prüfe ob DAILY_CREDIT_DEDUCTION positiv ist
        if credit_config.DAILY_CREDIT_DEDUCTION <= 0:
            print(f"FEHLER: DAILY_CREDIT_DEDUCTION muss positiv sein: {credit_config.DAILY_CREDIT_DEDUCTION}")
            return False
        
        # Prüfe ob LOW_CREDIT_WARNING_THRESHOLD sinnvoll ist
        if credit_config.LOW_CREDIT_WARNING_THRESHOLD < 0:
            print(f"FEHLER: LOW_CREDIT_WARNING_THRESHOLD muss nicht-negativ sein: {credit_config.LOW_CREDIT_WARNING_THRESHOLD}")
            return False
        
        print("Credit-Konfiguration ist gültig!")
        return True
        
    except Exception as e:
        print(f"FEHLER bei der Validierung der Credit-Konfiguration: {e}")
        return False


# =============================================================================
# BEISPIEL-VERWENDUNG UND DOKUMENTATION
# =============================================================================

if __name__ == "__main__":
    # Beispiel-Verwendung der Credit-Konfiguration
    print("=== BuildWise Credit Configuration ===")
    print()
    
    # Zeige alle Credit-Rewards
    print("Credit-Rewards:")
    for event_type, amount in credit_config.CREDIT_REWARDS.items():
        print(f"  {event_type.value}: {amount} Credits")
    
    print()
    
    # Zeige System-Parameter
    print("System-Parameter:")
    print(f"  Täglicher Abzug: {credit_config.DAILY_CREDIT_DEDUCTION} Credits")
    print(f"  Warnung bei: {credit_config.LOW_CREDIT_WARNING_THRESHOLD} Credits")
    print(f"  Min. Credits für Pro: {credit_config.MIN_CREDITS_FOR_PRO} Credits")
    
    print()
    
    # Zeige Feature-Flags
    print("Feature-Flags:")
    for feature, enabled in credit_config.FEATURE_FLAGS.items():
        print(f"  {feature}: {'[SUCCESS]' if enabled else '[ERROR]'}")
    
    print()
    
    # Validiere Konfiguration
    print("Validierung:")
    validate_credit_config()
    
    print()
    print("=== Beispiel: Konfiguration ändern ===")
    
    # Beispiel: Credit-Reward ändern
    old_reward = credit_config.get_credit_reward(CreditEventType.QUOTE_ACCEPTED)
    print(f"Alter Reward für QUOTE_ACCEPTED: {old_reward}")
    
    credit_config.update_credit_reward(CreditEventType.QUOTE_ACCEPTED, 7)
    new_reward = credit_config.get_credit_reward(CreditEventType.QUOTE_ACCEPTED)
    print(f"Neuer Reward für QUOTE_ACCEPTED: {new_reward}")
    
    # Beispiel: Feature togglen
    print(f"Besichtigungs-Bonus aktiviert: {credit_config.is_feature_enabled('enable_inspection_bonus')}")
    credit_config.toggle_feature('enable_inspection_bonus')
    print(f"Besichtigungs-Bonus nach Toggle: {credit_config.is_feature_enabled('enable_inspection_bonus')}")
