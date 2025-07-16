from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import List, Dict, Any
import logging

from app.models.buildwise_fee import BuildWiseFee
from app.models.user import User
from app.services.buildwise_fee_service import BuildWiseFeeService
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)

class MonthlyInvoiceService:
    def __init__(self, db: Session):
        self.db = db
        self.fee_service = BuildWiseFeeService(db)
        self.document_service = DocumentService(db)
    
    def create_monthly_invoices(self, month: int, year: int) -> Dict[str, Any]:
        """Erstelle monatliche Rechnungen für alle Benutzer mit offenen Gebühren"""
        logger.info(f"Erstelle monatliche Rechnungen für {month}/{year}")
        
        # Hole alle Benutzer mit offenen Gebühren
        users_with_fees = self.db.query(User).join(BuildWiseFee).filter(
            BuildWiseFee.fee_month == month,
            BuildWiseFee.fee_year == year,
            BuildWiseFee.status == "open"
        ).distinct().all()
        
        results = {
            "total_users": len(users_with_fees),
            "total_invoices_created": 0,
            "total_amount": 0,
            "errors": []
        }
        
        for user in users_with_fees:
            try:
                # Erstelle Rechnung für diesen Benutzer
                invoice_data = self.fee_service.create_monthly_invoice(user.id, month, year)
                
                if invoice_data:
                    results["total_invoices_created"] += 1
                    results["total_amount"] += invoice_data["total_amount"]
                    
                    # Erstelle Rechnungsdokument
                    self._create_invoice_document(user, invoice_data, month, year)
                    
                    logger.info(f"Rechnung für Benutzer {user.id} erstellt: {invoice_data['invoice_number']}")
                else:
                    logger.info(f"Keine offenen Gebühren für Benutzer {user.id}")
                    
            except Exception as e:
                error_msg = f"Fehler bei Rechnungserstellung für Benutzer {user.id}: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        logger.info(f"Monatliche Rechnungserstellung abgeschlossen: {results}")
        return results
    
    def _create_invoice_document(self, user: User, invoice_data: Dict[str, Any], month: int, year: int):
        """Erstelle ein Rechnungsdokument im Dokumentenbereich"""
        try:
            # Erstelle Rechnungstext
            invoice_text = self._generate_invoice_text(user, invoice_data, month, year)
            
            # Erstelle Dokument
            document_data = {
                "title": f"BuildWise-Gebührenrechnung {month:02d}/{year}",
                "description": f"Monatliche BuildWise-Gebührenrechnung für {month:02d}/{year}",
                "document_type": "invoice",
                "project_id": 1,  # Globales Projekt für Gebühren
                "category": "billing",
                "tags": "buildwise,gebühren,rechnung,monatlich",
                "is_public": False,
                "content": invoice_text
            }
            
            # Erstelle FormData für Dokument-Upload
            from io import BytesIO
            content_bytes = invoice_text.encode('utf-8')
            content_file = BytesIO(content_bytes)
            
            # Hier würde normalerweise das Dokument hochgeladen werden
            # Für jetzt nur Logging
            logger.info(f"Rechnungsdokument erstellt für Benutzer {user.id}: {document_data['title']}")
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Rechnungsdokuments: {str(e)}")
    
    def _generate_invoice_text(self, user: User, invoice_data: Dict[str, Any], month: int, year: int) -> str:
        """Generiere Rechnungstext"""
        month_names = [
            "Januar", "Februar", "März", "April", "Mai", "Juni",
            "Juli", "August", "September", "Oktober", "November", "Dezember"
        ]
        
        invoice_text = f"""
BUILDWISE GMBH
Gebührenrechnung

Rechnungsnummer: {invoice_data['invoice_number']}
Rechnungsdatum: {datetime.now().strftime('%d.%m.%Y')}
Fälligkeitsdatum: {invoice_data['due_date'].strftime('%d.%m.%Y')}

Rechnung an:
{user.first_name} {user.last_name}
{user.email}

Gebühren für {month_names[month-1]} {year}

Gesamtbetrag: {invoice_data['total_amount']:.2f}€
Anzahl Gebühren: {invoice_data['fee_count']}

Die Gebühren basieren auf 1% der akzeptierten Angebote/Kostenvoranschläge.

Bitte überweisen Sie den Betrag innerhalb von 14 Tagen auf unser Konto.

Vielen Dank für Ihr Vertrauen!

BuildWise GmbH
        """
        
        return invoice_text.strip()
    
    def check_overdue_invoices(self) -> Dict[str, Any]:
        """Prüfe überfällige Rechnungen und markiere sie als overdue"""
        logger.info("Prüfe überfällige Rechnungen")
        
        # Finde Rechnungen, die überfällig sind (älter als 28 Tage)
        overdue_date = datetime.now().replace(day=28)
        overdue_fees = self.db.query(BuildWiseFee).filter(
            BuildWiseFee.status == "open",
            BuildWiseFee.due_date < overdue_date
        ).all()
        
        results = {
            "total_overdue": len(overdue_fees),
            "updated_fees": 0,
            "errors": []
        }
        
        for fee in overdue_fees:
            try:
                fee.status = "overdue"
                self.db.commit()
                results["updated_fees"] += 1
                logger.info(f"Gebühr {fee.id} als überfällig markiert")
            except Exception as e:
                error_msg = f"Fehler beim Markieren der überfälligen Gebühr {fee.id}: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        logger.info(f"Überfällige Rechnungen geprüft: {results}")
        return results 