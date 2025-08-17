# Intelligente Dokumentenkategorisierung für das DMS
# Backend-Version der automatischen Kategorisierung

import re
from typing import Optional, Dict, List

class DocumentCategorizer:
    """Automatische Dokumentenkategorisierung für das DMS"""
    
    # Kategorisierungs-Regeln für verschiedene Dokumenttypen
    CATEGORY_PATTERNS = {
        'finance': {
            'patterns': [
                r'rechnung',
                r'invoice',
                r'kostenvoranschlag',
                r'angebot',
                r'kalkulation',
                r'leistungsverzeichnis',
                r'zahlung',
                r'beleg',
                r'quittung',
                r'schlussrechnung',
                r'abrechnung',
                r'budget'
            ],
            'subcategories': {
                'Rechnungen': ['rechnung', 'invoice', 'faktura'],
                'Bezahlte Rechnungen': ['bezahlt', 'paid'],
                'Kostenvoranschläge': ['kostenvoranschlag', 'angebot', 'kalkulation'],
                'Manuelle Rechnungen': ['manuell', 'manual'],
                'Hochgeladene Rechnungen': ['upload', 'hochgeladen'],
                'Zahlungsbelege': ['zahlung', 'beleg', 'quittung', 'überweisung'],
                'Schlussrechnungen': ['schlussrechnung', 'endabrechnung', 'final']
            }
        },
        'planning': {
            'patterns': [
                r'grundriss',
                r'bauplan',
                r'lageplan',
                r'schnitt',
                r'ansicht',
                r'detail',
                r'genehmigung',
                r'baugenehmigung',
                r'bauantrag',
                r'statik',
                r'tragwerk',
                r'energieausweis',
                r'vermessung'
            ],
            'subcategories': {
                'Baupläne & Grundrisse': ['grundriss', 'plan', 'lageplan'],
                'Baugenehmigungen': ['genehmigung', 'bauantrag', 'behörde'],
                'Statische Berechnungen': ['statik', 'tragwerk', 'berechnung']
            }
        },
        'contracts': {
            'patterns': [
                r'vertrag',
                r'bauvertrag',
                r'nachtrag',
                r'versicherung',
                r'gewährleistung',
                r'mängel',
                r'rüge',
                r'rechtlich'
            ],
            'subcategories': {
                'Bauverträge': ['bauvertrag', 'hauptvertrag', 'werkvertrag'],
                'Nachträge': ['nachtrag', 'änderung', 'zusatz'],
                'Versicherungen': ['versicherung', 'police', 'haftung']
            }
        }
    }
    
    @classmethod
    def categorize_document(cls, filename: str, file_extension: str = ".pdf") -> Optional[str]:
        """Kategorisiert ein Dokument basierend auf dem Dateinamen"""
        filename_lower = filename.lower()
        
        # Suche nach der besten Kategorie-Übereinstimmung
        best_match = None
        best_score = 0
        
        for category, data in cls.CATEGORY_PATTERNS.items():
            score = 0
            for pattern in data['patterns']:
                if re.search(pattern, filename_lower):
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = category
        
        return best_match
    
    @classmethod
    def suggest_subcategory(cls, category: Optional[str], filename: str, invoice_status: str = None, invoice_type: str = None) -> str:
        """Schlägt eine Subkategorie basierend auf der Hauptkategorie vor"""
        if not category or category not in cls.CATEGORY_PATTERNS:
            return "Sonstige"
        
        filename_lower = filename.lower()
        subcategories = cls.CATEGORY_PATTERNS[category]['subcategories']
        
        # Spezielle Logik für Rechnungen basierend auf Status und Typ
        if category == 'finance':
            if invoice_status == 'paid':
                return "Bezahlte Rechnungen"
            elif invoice_type == 'MANUAL':
                return "Manuelle Rechnungen"
            elif invoice_type == 'UPLOAD':
                return "Hochgeladene Rechnungen"
        
        # Standard-Subkategorisierung basierend auf Dateinamen
        for subcategory, keywords in subcategories.items():
            for keyword in keywords:
                if keyword in filename_lower:
                    return subcategory
        
        # Fallback für Finanzdokumente
        if category == 'finance':
            return "Rechnungen"
        
        return "Sonstige"
    
    @classmethod
    def generate_tags(cls, filename: str, milestone_title: str, service_provider_name: str, 
                     amount: float, status: str, invoice_type: str) -> List[str]:
        """Generiert intelligente Tags für das Dokument"""
        tags = [
            "Rechnung",
            "Finanzen",
            milestone_title,
            f"Betrag_{int(amount)}EUR",
            f"Status_{status}",
            f"Dienstleister_{service_provider_name}".replace(" ", "_")
        ]
        
        # Status-spezifische Tags
        if status == 'paid':
            tags.append("Bezahlt")
        elif status == 'overdue':
            tags.append("Überfällig")
        
        # Typ-spezifische Tags
        if invoice_type == 'MANUAL':
            tags.append("Manuell_erstellt")
        elif invoice_type == 'UPLOAD':
            tags.append("PDF_Upload")
        
        # Betragskategorien
        if amount >= 10000:
            tags.append("Großauftrag")
        elif amount >= 5000:
            tags.append("Mittelauftrag")
        else:
            tags.append("Kleinauftrag")
        
        return tags
