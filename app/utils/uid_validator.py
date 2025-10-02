"""
UID (Umsatzsteuer-Identifikationsnummer) Validierung für deutsche Rechnungen
"""
import re
from typing import Optional, Tuple


class UIDValidator:
    """Validierung von USt-ID und Steuernummern"""
    
    # Deutsche USt-ID Format: DE + 9 Ziffern
    DE_UID_PATTERN = re.compile(r'^DE\d{9}$')
    
    # Deutsche Steuernummer Format (verschiedene Bundesländer)
    DE_TAX_PATTERN = re.compile(r'^\d{2,3}\/\d{2,3}\/\d{4,5}$')
    
    @staticmethod
    def validate_german_uid(uid: str) -> Tuple[bool, str]:
        """
        Validiert deutsche USt-ID
        
        Args:
            uid: USt-ID zum Validieren
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not uid:
            return True, ""  # Leer ist erlaubt (optional)
        
        uid = uid.strip().upper()
        
        if not UIDValidator.DE_UID_PATTERN.match(uid):
            return False, "Deutsche USt-ID muss im Format DE123456789 sein (DE + 9 Ziffern)"
        
        # Prüfziffer-Validierung für deutsche USt-ID
        if not UIDValidator._validate_german_uid_checksum(uid):
            return False, "Ungültige Prüfziffer in der deutschen USt-ID"
        
        return True, ""
    
    @staticmethod
    def validate_german_tax_number(tax_number: str) -> Tuple[bool, str]:
        """
        Validiert deutsche Steuernummer
        
        Args:
            tax_number: Steuernummer zum Validieren
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not tax_number:
            return True, ""  # Leer ist erlaubt (optional)
        
        tax_number = tax_number.strip()
        
        if not UIDValidator.DE_TAX_PATTERN.match(tax_number):
            return False, "Deutsche Steuernummer muss im Format 12/345/67890 sein"
        
        return True, ""
    
    @staticmethod
    def _validate_german_uid_checksum(uid: str) -> bool:
        """
        Validiert die Prüfziffer einer deutschen USt-ID
        
        Args:
            uid: USt-ID im Format DE123456789
            
        Returns:
            bool: True wenn Prüfziffer korrekt
        """
        try:
            # Entferne DE-Präfix
            digits = uid[2:]
            
            # Gewichtung für Prüfziffer-Berechnung
            weights = [1, 2, 1, 2, 1, 2, 1, 2, 1]
            
            # Berechne gewichtete Summe
            weighted_sum = 0
            for i, digit in enumerate(digits):
                product = int(digit) * weights[i]
                # Quersumme von Produkten > 9
                if product > 9:
                    product = sum(int(d) for d in str(product))
                weighted_sum += product
            
            # Prüfziffer ist die letzte Ziffer der gewichteten Summe
            checksum = weighted_sum % 10
            
            # Bei Checksum 0 ist die Prüfziffer 0, sonst 10 - checksum
            expected_checksum = 0 if checksum == 0 else 10 - checksum
            
            return expected_checksum == int(digits[-1])
            
        except (ValueError, IndexError):
            return False
    
    @staticmethod
    def format_uid_for_display(uid: str) -> str:
        """
        Formatiert USt-ID für Anzeige
        
        Args:
            uid: USt-ID
            
        Returns:
            str: Formatierte USt-ID
        """
        if not uid:
            return ""
        
        uid = uid.strip().upper()
        
        # Deutsche USt-ID: DE123456789 -> DE 123 456 789
        if uid.startswith('DE') and len(uid) == 11:
            return f"{uid[:2]} {uid[2:5]} {uid[5:8]} {uid[8:]}"
        
        return uid
    
    @staticmethod
    def format_tax_number_for_display(tax_number: str) -> str:
        """
        Formatiert Steuernummer für Anzeige
        
        Args:
            tax_number: Steuernummer
            
        Returns:
            str: Formatierte Steuernummer
        """
        if not tax_number:
            return ""
        
        return tax_number.strip()


class InvoiceUIDRequirements:
    """Bestimmt UID-Anzeige-Anforderungen für Rechnungen"""
    
    @staticmethod
    def requires_seller_uid(invoice_amount: float, is_small_business: bool = False) -> bool:
        """
        Bestimmt ob Rechnungssteller USt-ID angeben muss
        
        Args:
            invoice_amount: Rechnungsbetrag (brutto)
            is_small_business: Ist Kleinunternehmer
            
        Returns:
            bool: True wenn USt-ID erforderlich
        """
        # Kleinunternehmer sind von der USt-ID-Pflicht befreit
        if is_small_business:
            return False
        
        # Bei Rechnungen über 10.000€ brutto ist USt-ID erforderlich
        return invoice_amount >= 10000.0
    
    @staticmethod
    def requires_buyer_uid(invoice_amount: float, is_eu_cross_border: bool = False) -> bool:
        """
        Bestimmt ob Rechnungsempfänger USt-ID angeben muss
        
        Args:
            invoice_amount: Rechnungsbetrag (brutto)
            is_eu_cross_border: Ist EU-Auslandsgeschäft
            
        Returns:
            bool: True wenn USt-ID erforderlich
        """
        # Bei EU-Auslandsgeschäften ist USt-ID immer erforderlich
        if is_eu_cross_border:
            return True
        
        # Bei Rechnungen über 10.000€ brutto ist USt-ID erforderlich
        return invoice_amount >= 10000.0
    
    @staticmethod
    def get_uid_display_requirements(
        invoice_amount: float,
        seller_is_small_business: bool = False,
        is_eu_cross_border: bool = False
    ) -> dict:
        """
        Bestimmt alle UID-Anzeige-Anforderungen für eine Rechnung
        
        Args:
            invoice_amount: Rechnungsbetrag (brutto)
            seller_is_small_business: Ist Rechnungssteller Kleinunternehmer
            is_eu_cross_border: Ist EU-Auslandsgeschäft
            
        Returns:
            dict: Anzeige-Anforderungen
        """
        return {
            'seller_uid_required': InvoiceUIDRequirements.requires_seller_uid(
                invoice_amount, seller_is_small_business
            ),
            'buyer_uid_required': InvoiceUIDRequirements.requires_buyer_uid(
                invoice_amount, is_eu_cross_border
            ),
            'seller_tax_number_required': not seller_is_small_business,  # Steuernummer immer erforderlich außer bei Kleinunternehmern
            'amount_threshold_exceeded': invoice_amount >= 10000.0,
            'is_eu_cross_border': is_eu_cross_border
        }
