#!/usr/bin/env python3
"""
PDF-Generator für BuildWise-Rechnungen
"""

import os
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

class BuildWisePDFGenerator:
    """Generiert PDF-Rechnungen für BuildWise-Gebühren"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Erstellt benutzerdefinierte Styles für die Rechnung"""
        
        # Header-Style
        self.styles.add(ParagraphStyle(
            name='Header',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=HexColor('#2c3539')
        ))
        
        # Subheader-Style
        self.styles.add(ParagraphStyle(
            name='SubHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            textColor=HexColor('#ffbd59')
        ))
        
        # Normal-Style
        self.styles.add(ParagraphStyle(
            name='Normal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=12
        ))
        
        # Small-Style
        self.styles.add(ParagraphStyle(
            name='Small',
            parent=self.styles['Normal'],
            fontSize=8,
            spaceAfter=6
        ))
    
    def generate_invoice_pdf(
        self,
        fee_data: dict,
        project_data: dict,
        quote_data: dict,
        cost_position_data: dict,
        output_path: str
    ) -> bool:
        """
        Generiert eine PDF-Rechnung für eine BuildWise-Gebühr
        
        Args:
            fee_data: Gebühren-Daten
            project_data: Projekt-Daten
            quote_data: Angebot-Daten
            cost_position_data: Kostenposition-Daten
            output_path: Ausgabepfad für die PDF
            
        Returns:
            bool: True wenn erfolgreich, False sonst
        """
        
        try:
            # Erstelle Verzeichnis falls nicht vorhanden
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Erstelle PDF-Dokument
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            # Story für PDF-Inhalt
            story = []
            
            # Header
            story.append(Paragraph("BUILDWISE GMBH", self.styles['Header']))
            story.append(Spacer(1, 20))
            
            # Rechnungsinformationen
            invoice_info = [
                ["Rechnungsnummer:", fee_data.get('invoice_number', f"BW-{fee_data['id']:06d}")],
                ["Rechnungsdatum:", self._format_date(fee_data.get('invoice_date'))],
                ["Fälligkeitsdatum:", self._format_date(fee_data.get('due_date'))],
                ["Status:", self._get_status_label(fee_data.get('status', 'open'))]
            ]
            
            invoice_table = Table(invoice_info, colWidths=[4*cm, 8*cm])
            invoice_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(invoice_table)
            story.append(Spacer(1, 20))
            
            # Projekt-Informationen
            story.append(Paragraph("Projekt-Informationen", self.styles['SubHeader']))
            project_info = [
                ["Projekt:", project_data.get('name', 'N/A')],
                ["Projekt-ID:", str(project_data.get('id', 'N/A'))],
                ["Projekt-Typ:", project_data.get('project_type', 'N/A')],
                ["Status:", project_data.get('status', 'N/A')],
                ["Budget:", self._format_currency(project_data.get('budget', 0))],
                ["Adresse:", project_data.get('address', 'N/A')]
            ]
            
            project_table = Table(project_info, colWidths=[4*cm, 8*cm])
            project_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(project_table)
            story.append(Spacer(1, 20))
            
            # Kostenposition-Informationen
            story.append(Paragraph("Kostenposition", self.styles['SubHeader']))
            cost_position_info = [
                ["Titel:", cost_position_data.get('title', 'N/A')],
                ["Beschreibung:", cost_position_data.get('description', 'N/A')],
                ["Betrag:", self._format_currency(cost_position_data.get('amount', 0))],
                ["Kategorie:", cost_position_data.get('category', 'N/A')],
                ["Status:", cost_position_data.get('status', 'N/A')],
                ["Dienstleister:", cost_position_data.get('contractor_name', 'N/A')]
            ]
            
            cost_position_table = Table(cost_position_info, colWidths=[4*cm, 8*cm])
            cost_position_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(cost_position_table)
            story.append(Spacer(1, 20))
            
            # Angebot-Informationen
            story.append(Paragraph("Angebot-Details", self.styles['SubHeader']))
            quote_info = [
                ["Angebot-ID:", str(quote_data.get('id', 'N/A'))],
                ["Titel:", quote_data.get('title', 'N/A')],
                ["Angebotsbetrag:", self._format_currency(quote_data.get('total_amount', 0))],
                ["Währung:", quote_data.get('currency', 'EUR')],
                ["Gültig bis:", self._format_date(quote_data.get('valid_until'))],
                ["Dienstleister:", quote_data.get('company_name', 'N/A')],
                ["Kontakt:", quote_data.get('contact_person', 'N/A')],
                ["E-Mail:", quote_data.get('email', 'N/A')],
                ["Telefon:", quote_data.get('phone', 'N/A')]
            ]
            
            quote_table = Table(quote_info, colWidths=[4*cm, 8*cm])
            quote_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(quote_table)
            story.append(Spacer(1, 20))
            
            # Gebühren-Berechnung
            story.append(Paragraph("BuildWise-Gebühren-Berechnung", self.styles['SubHeader']))
            
            # Berechne Steuer
            net_amount = fee_data.get('fee_amount', 0)
            tax_rate = fee_data.get('tax_rate', 19.0)
            tax_amount = net_amount * (tax_rate / 100)
            gross_amount = net_amount + tax_amount
            
            fee_calculation = [
                ["Netto-Betrag:", self._format_currency(net_amount)],
                ["Steuersatz:", f"{tax_rate}%"],
                ["Steuerbetrag:", self._format_currency(tax_amount)],
                ["Brutto-Betrag:", self._format_currency(gross_amount)]
            ]
            
            fee_table = Table(fee_calculation, colWidths=[4*cm, 8*cm])
            fee_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ]))
            story.append(fee_table)
            story.append(Spacer(1, 20))
            
            # Zusätzliche Informationen
            if fee_data.get('notes'):
                story.append(Paragraph("Zusätzliche Informationen", self.styles['SubHeader']))
                story.append(Paragraph(fee_data['notes'], self.styles['Normal']))
                story.append(Spacer(1, 20))
            
            # Footer
            story.append(Spacer(1, 30))
            footer_text = """
            <b>BuildWise GmbH</b><br/>
            Musterstraße 123<br/>
            12345 Musterstadt<br/>
            Deutschland<br/><br/>
            
            <b>Kontakt:</b><br/>
            E-Mail: info@buildwise.de<br/>
            Telefon: +49 123 456789<br/>
            Website: www.buildwise.de<br/><br/>
            
            <b>Bankverbindung:</b><br/>
            IBAN: DE12 3456 7890 1234 5678 90<br/>
            BIC: DEUTDEDB123<br/>
            Bank: Deutsche Bank AG
            """
            story.append(Paragraph(footer_text, self.styles['Small']))
            
            # Erstelle PDF
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"Fehler beim Generieren der PDF: {e}")
            return False
    
    def _format_date(self, date_string: Optional[str]) -> str:
        """Formatiert ein Datum"""
        if not date_string:
            return "N/A"
        try:
            if isinstance(date_string, str):
                date_obj = datetime.strptime(date_string, "%Y-%m-%d").date()
            else:
                date_obj = date_string
            return date_obj.strftime("%d.%m.%Y")
        except:
            return "N/A"
    
    def _format_currency(self, amount: float) -> str:
        """Formatiert einen Betrag als Währung"""
        try:
            return f"{amount:,.2f} €"
        except:
            return "0,00 €"
    
    def _get_status_label(self, status: str) -> str:
        """Gibt den deutschen Status-Label zurück"""
        status_labels = {
            'open': 'Offen',
            'paid': 'Bezahlt',
            'overdue': 'Überfällig',
            'cancelled': 'Storniert'
        }
        return status_labels.get(status, status) 