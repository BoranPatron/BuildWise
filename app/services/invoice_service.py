"""
Invoice service for construction billing and payment management
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, and_, or_, text
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import os
import uuid
from pathlib import Path

from app.models import (
    Invoice, InvoiceStatus, InvoiceType, CostPosition,
    Milestone, User, Project, Quote, QuoteStatus
)
from app.schemas.invoice import (
    InvoiceCreate, InvoiceUpdate, InvoiceUpload, 
    InvoicePayment, InvoiceRating, InvoiceStats
)
from app.core.config import settings
from app.utils.uid_validator import UIDValidator, InvoiceUIDRequirements

class InvoiceService:
    
    @staticmethod
    async def create_manual_invoice(
        db: AsyncSession,
        invoice_data: InvoiceCreate,
        created_by_user_id: int
    ) -> Invoice:
        """Erstelle eine manuelle Rechnung"""
        
        # Validiere dass der Meilenstein existiert
        milestone = await db.get(Milestone, invoice_data.milestone_id)
        if not milestone:
            raise ValueError(f"Meilenstein mit ID {invoice_data.milestone_id} nicht gefunden")
        
        # Validiere dass es ein akzeptiertes Quote für diesen Meilenstein gibt
        quote_query = select(Quote).where(
            and_(
                Quote.milestone_id == invoice_data.milestone_id,
                Quote.status == QuoteStatus.ACCEPTED
            )
        )
        result = await db.execute(quote_query)
        quote = result.scalar_one_or_none()
        
        if not quote:
            raise ValueError(f"Kein akzeptiertes Angebot für Meilenstein {invoice_data.milestone_id} gefunden")
        
        # Prüfe ob bereits eine Rechnung für diesen Meilenstein existiert
        existing_invoice_query = select(Invoice).where(
            Invoice.milestone_id == invoice_data.milestone_id
        )
        result = await db.execute(existing_invoice_query)
        existing_invoice = result.scalar_one_or_none()
        
        # Wenn eine Rechnung existiert, überschreibe diese statt eine neue zu erstellen
        if existing_invoice:
            print(f"✅ Bestehende Rechnung für Meilenstein {invoice_data.milestone_id} wird überschrieben")
            
            # Lösche alle existierenden Kostenpositionen - verwende direkte SQL-Abfrage mit text()
            # ohne auf die Relation cost_positions zuzugreifen
            delete_query = text(f"DELETE FROM cost_positions WHERE invoice_id = {existing_invoice.id}")
            await db.execute(delete_query)
            await db.flush()
                
            # Aktualisiere bestehende Rechnung mit den neuen Daten
            existing_invoice.invoice_number = invoice_data.invoice_number
            existing_invoice.invoice_date = invoice_data.invoice_date
            existing_invoice.due_date = invoice_data.due_date
            existing_invoice.net_amount = invoice_data.net_amount
            existing_invoice.vat_rate = invoice_data.vat_rate
            existing_invoice.vat_amount = invoice_data.vat_amount
            existing_invoice.total_amount = invoice_data.total_amount
            existing_invoice.material_costs = invoice_data.material_costs or 0.0
            existing_invoice.labor_costs = invoice_data.labor_costs or 0.0
            existing_invoice.additional_costs = invoice_data.additional_costs or 0.0
            existing_invoice.description = invoice_data.description
            existing_invoice.work_period_from = invoice_data.work_period_from
            existing_invoice.work_period_to = invoice_data.work_period_to
            existing_invoice.notes = invoice_data.notes
            existing_invoice.updated_at = datetime.utcnow()
            
            invoice = existing_invoice
            
        else:
            # Erstelle eine neue Rechnung
            print(f"✅ Neue Rechnung für Meilenstein {invoice_data.milestone_id} wird erstellt")
            invoice = Invoice(
                project_id=invoice_data.project_id,
                milestone_id=invoice_data.milestone_id,
                service_provider_id=invoice_data.service_provider_id,
                invoice_number=invoice_data.invoice_number,
                invoice_date=invoice_data.invoice_date,
                due_date=invoice_data.due_date,
                net_amount=invoice_data.net_amount,
                vat_rate=invoice_data.vat_rate,
                vat_amount=invoice_data.vat_amount,
                total_amount=invoice_data.total_amount,
                material_costs=invoice_data.material_costs or 0.0,
                labor_costs=invoice_data.labor_costs or 0.0,
                additional_costs=invoice_data.additional_costs or 0.0,
                description=invoice_data.description,
                work_period_from=invoice_data.work_period_from,
                work_period_to=invoice_data.work_period_to,
                type=InvoiceType.MANUAL,
                notes=invoice_data.notes,
                status=InvoiceStatus.SENT,  # Manuelle Rechnungen sind sofort "gesendet"
                created_by=created_by_user_id
            )
            db.add(invoice)
        
        # Nur bei neuer Rechnung nochmals hinzufügen, bestehende wurde bereits aktualisiert
        await db.flush()  # Flush um die invoice.id zu bekommen
        
        # ✅ Erstelle flexible Kostenpositionen
        if hasattr(invoice_data, 'cost_positions') and invoice_data.cost_positions:
            for idx, cost_pos in enumerate(invoice_data.cost_positions):
                cost_position = CostPosition(
                    invoice_id=invoice.id,
                    title=cost_pos.description,  # Verwende description als title
                    description=cost_pos.description,
                    amount=cost_pos.amount,
                    position_order=idx,
                    category=cost_pos.category if hasattr(cost_pos, 'category') else "custom",
                    cost_type=cost_pos.cost_type if hasattr(cost_pos, 'cost_type') else "standard",
                    status=cost_pos.status if hasattr(cost_pos, 'status') else "active"
                )
                db.add(cost_position)
        else:
            # Fallback: Erstelle Standard-Kostenpositionen aus Legacy-Feldern
            if invoice_data.material_costs and invoice_data.material_costs > 0:
                cost_position = CostPosition(
                    invoice_id=invoice.id,
                    title="Materialkosten",
                    description="Materialkosten",
                    amount=invoice_data.material_costs,
                    position_order=0,
                    category="material",
                    cost_type="standard",
                    status="active"
                )
                db.add(cost_position)
            
            if invoice_data.labor_costs and invoice_data.labor_costs > 0:
                cost_position = CostPosition(
                    invoice_id=invoice.id,
                    title="Arbeitskosten",
                    description="Arbeitskosten",
                    amount=invoice_data.labor_costs,
                    position_order=1,
                    category="labor",
                    cost_type="standard",
                    status="active"
                )
                db.add(cost_position)
            
            if invoice_data.additional_costs and invoice_data.additional_costs > 0:
                cost_position = CostPosition(
                    invoice_id=invoice.id,
                    title="Zusatzkosten",
                    description="Zusatzkosten",
                    amount=invoice_data.additional_costs,
                    position_order=2,
                    category="other",
                    cost_type="additional",
                    status="active"
                )
                db.add(cost_position)
        
        await db.commit()
        await db.refresh(invoice)
        
        # ✅ Generiere PDF sofort bei Erstellung
        try:
            print(f"🔍 Generiere PDF für neue manuelle Rechnung {invoice.id}")
            pdf_path = await InvoiceService.generate_invoice_pdf(db, invoice.id)
            
            # Update invoice mit PDF-Pfad
            invoice.pdf_file_path = pdf_path
            invoice.pdf_file_name = f"Rechnung_{invoice.invoice_number}.pdf"
            await db.commit()
            await db.refresh(invoice)
            
            print(f"✅ PDF sofort generiert: {pdf_path}")
            
            # ✅ Automatische DMS-Integration
            try:
                await InvoiceService.create_dms_document(db, invoice, pdf_path)
                print(f"✅ DMS-Dokument erstellt für neue Rechnung {invoice.id}")
            except Exception as dms_error:
                print(f"⚠️ DMS-Integration fehlgeschlagen (nicht kritisch): {dms_error}")
                
        except Exception as pdf_error:
            print(f"⚠️ PDF-Generierung bei Erstellung fehlgeschlagen: {pdf_error}")
            # PDF-Fehler blockiert nicht die Rechnungserstellung
        
        print(f"✅ Manuelle Rechnung erstellt: {invoice.invoice_number} für Meilenstein {milestone.title}")
        
        return invoice
    
    @staticmethod
    async def upload_invoice_pdf(
        db: AsyncSession,
        invoice_data: InvoiceUpload,
        pdf_file: bytes,
        original_filename: str,
        created_by_user_id: int
    ) -> Invoice:
        """Lade eine PDF-Rechnung hoch"""
        
        # Validiere dass der Meilenstein existiert
        milestone = await db.get(Milestone, invoice_data.milestone_id)
        if not milestone:
            raise ValueError(f"Meilenstein mit ID {invoice_data.milestone_id} nicht gefunden")
        
        # Prüfe ob bereits eine Rechnung für diesen Meilenstein existiert
        existing_invoice_query = select(Invoice).where(
            Invoice.milestone_id == invoice_data.milestone_id
        )
        result = await db.execute(existing_invoice_query)
        existing_invoice = result.scalar_one_or_none()
        
        # Wenn eine Rechnung existiert, lösche vorhandene Kostenpositionen
        if existing_invoice:
            print(f"✅ Bestehende Rechnung für Meilenstein {invoice_data.milestone_id} wird überschrieben")
            # Verwende text() für direkte SQL-Abfragen
            delete_query = text(f"DELETE FROM cost_positions WHERE invoice_id = {existing_invoice.id}")
            await db.execute(delete_query)
            await db.flush()
        
        # Speichere die PDF-Datei projektbasiert
        project_dir = Path(f"storage/invoices/project_{milestone.project_id}")
        upload_dir = project_dir
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generiere einen eindeutigen Dateinamen
        file_extension = Path(original_filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = upload_dir / unique_filename
        
        with open(file_path, "wb") as f:
            f.write(pdf_file)
        
        # Hole Projekt- und Service-Provider-Informationen
        project = await db.get(Project, milestone.project_id)
        service_provider_query = select(Quote).where(
            and_(
                Quote.milestone_id == invoice_data.milestone_id,
                Quote.status == QuoteStatus.ACCEPTED
            )
        ).options(selectinload(Quote.service_provider))
        result = await db.execute(service_provider_query)
        quote = result.scalar_one_or_none()
        
        if not quote:
            raise ValueError(f"Kein akzeptiertes Angebot für Meilenstein {invoice_data.milestone_id} gefunden")
        
        # Wenn eine Rechnung existiert, überschreibe diese statt eine neue zu erstellen
        if existing_invoice:
            print(f"✅ Bestehende Rechnung für Meilenstein {invoice_data.milestone_id} wird überschrieben")
            
            # Update die bestehenden Felder
            existing_invoice.invoice_number = invoice_data.invoice_number
            existing_invoice.pdf_file_path = str(file_path)
            existing_invoice.pdf_file_name = original_filename
            existing_invoice.total_amount = invoice_data.total_amount
            existing_invoice.net_amount = invoice_data.total_amount / 1.19  # Annahme: 19% MwSt.
            existing_invoice.vat_amount = invoice_data.total_amount - (invoice_data.total_amount / 1.19)
            existing_invoice.notes = invoice_data.notes
            existing_invoice.updated_at = datetime.utcnow()
            
            invoice = existing_invoice
            
        else:
            # Erstelle eine neue Rechnung
            print(f"✅ Neue Rechnung für Meilenstein {invoice_data.milestone_id} wird erstellt")
            invoice = Invoice(
            project_id=milestone.project_id,
            milestone_id=invoice_data.milestone_id,
            service_provider_id=quote.service_provider_id,
            invoice_number=invoice_data.invoice_number,
            invoice_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=30),  # Standard: 30 Tage Zahlungsziel
            net_amount=invoice_data.total_amount / 1.19,  # Annahme: 19% MwSt.
            vat_rate=19.0,
            vat_amount=invoice_data.total_amount - (invoice_data.total_amount / 1.19),
            total_amount=invoice_data.total_amount,
            type=InvoiceType.UPLOAD,
            pdf_file_path=str(file_path),
            pdf_file_name=original_filename,
            notes=invoice_data.notes,
            status=InvoiceStatus.SENT,
            created_by=created_by_user_id
        )
        
        # Nur neue Rechnung hinzufügen, bestehende ist bereits in der DB
        if not existing_invoice:
            db.add(invoice)
            
        await db.commit()
        await db.refresh(invoice)
        
        # ✅ Automatische DMS-Integration für hochgeladene PDFs
        await InvoiceService.create_dms_document(db, invoice, str(file_path))
        
        print(f"✅ PDF-Rechnung hochgeladen: {invoice.invoice_number} für Meilenstein {milestone.title}")
        return invoice
    
    @staticmethod
    async def generate_invoice_pdf(db: AsyncSession, invoice_id: int) -> str:
        """Generiere eine PDF-Rechnung aus den Rechnungsdaten"""
        
        # Lade die Rechnung mit allen Beziehungen
        invoice_query = select(Invoice).options(
            selectinload(Invoice.milestone).selectinload(Milestone.project).selectinload(Project.owner),
            selectinload(Invoice.service_provider),
            selectinload(Invoice.cost_positions)  # ✅ Lade auch die Kostenpositionen
        ).where(Invoice.id == invoice_id)
        
        result = await db.execute(invoice_query)
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            raise ValueError(f"Rechnung mit ID {invoice_id} nicht gefunden")
        
        # Erstelle PDF-Verzeichnis projektbasiert
        pdf_dir = Path(f"storage/invoices/project_{invoice.project_id}")
        pdf_dir.mkdir(parents=True, exist_ok=True)
        
        # Generiere PDF-Dateiname
        pdf_filename = f"Rechnung_{invoice.invoice_number}_{invoice_id}.pdf"
        pdf_path = pdf_dir / pdf_filename
        
        # ✅ Einfache PDF-Generierung mit ReportLab
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib import colors
            from reportlab.pdfgen import canvas
            
            # Erstelle PDF-Dokument
            doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
            story = []
            styles = getSampleStyleSheet()
            
            # Titel
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=20,
                alignment=1  # Zentriert
            )
            story.append(Paragraph(f"RECHNUNG {invoice.invoice_number}", title_style))
            story.append(Spacer(1, 20))
            
            # Bauträger-Kontaktdaten (Rechnungsempfänger)
            bautraeger = invoice.milestone.project.owner if invoice.milestone.project.owner else None
            
            story.append(Paragraph("Rechnungsempfänger:", styles['Heading3']))
            if bautraeger:
                bautraeger_info = f"{bautraeger.first_name} {bautraeger.last_name}"
                if bautraeger.company_name:
                    bautraeger_info = f"{bautraeger.company_name}<br/>{bautraeger_info}"
                
                # Adressinformationen hinzufügen
                address_parts = []
                if bautraeger.address_street:
                    address_parts.append(bautraeger.address_street)
                if bautraeger.address_zip and bautraeger.address_city:
                    address_parts.append(f"{bautraeger.address_zip} {bautraeger.address_city}")
                elif bautraeger.address_city:
                    address_parts.append(bautraeger.address_city)
                if bautraeger.address_country and bautraeger.address_country != "Deutschland":
                    address_parts.append(bautraeger.address_country)
                
                if address_parts:
                    bautraeger_info += f"<br/>{'<br/>'.join(address_parts)}"
                
                # UID-Anzeige für Rechnungsempfänger
                uid_requirements = InvoiceUIDRequirements.get_uid_display_requirements(
                    invoice_amount=invoice.total_amount,
                    seller_is_small_business=getattr(invoice.service_provider, 'is_small_business', False),
                    is_eu_cross_border=False  # TODO: Implementiere EU-Erkennung
                )
                
                if uid_requirements['buyer_uid_required'] and bautraeger.company_uid:
                    bautraeger_info += f"<br/>USt-ID: {UIDValidator.format_uid_for_display(bautraeger.company_uid)}"
                elif uid_requirements['buyer_uid_required'] and bautraeger.company_tax_number:
                    bautraeger_info += f"<br/>Steuernummer: {UIDValidator.format_tax_number_for_display(bautraeger.company_tax_number)}"
                
                if bautraeger.email:
                    bautraeger_info += f"<br/>{bautraeger.email}"
                if bautraeger.phone:
                    bautraeger_info += f"<br/>{bautraeger.phone}"
                story.append(Paragraph(bautraeger_info, styles['Normal']))
            else:
                story.append(Paragraph("Bauträger-Daten nicht verfügbar", styles['Normal']))
            
            story.append(Spacer(1, 20))
            
            # Dienstleister-Kontaktdaten (Rechnungssteller)
            story.append(Paragraph("Rechnungssteller:", styles['Heading3']))
            dienstleister_info = f"{invoice.service_provider.first_name} {invoice.service_provider.last_name}"
            if invoice.service_provider.company_name:
                dienstleister_info = f"{invoice.service_provider.company_name}<br/>{dienstleister_info}"
            
            # Adressinformationen hinzufügen
            address_parts = []
            if invoice.service_provider.address_street:
                address_parts.append(invoice.service_provider.address_street)
            if invoice.service_provider.address_zip and invoice.service_provider.address_city:
                address_parts.append(f"{invoice.service_provider.address_zip} {invoice.service_provider.address_city}")
            elif invoice.service_provider.address_city:
                address_parts.append(invoice.service_provider.address_city)
            if invoice.service_provider.address_country and invoice.service_provider.address_country != "Deutschland":
                address_parts.append(invoice.service_provider.address_country)
            
            if address_parts:
                dienstleister_info += f"<br/>{'<br/>'.join(address_parts)}"
            
            # UID-Anzeige für Rechnungssteller
            uid_requirements = InvoiceUIDRequirements.get_uid_display_requirements(
                invoice_amount=invoice.total_amount,
                seller_is_small_business=getattr(invoice.service_provider, 'is_small_business', False),
                is_eu_cross_border=False  # TODO: Implementiere EU-Erkennung
            )
            
            # Rechnungssteller muss immer USt-ID oder Steuernummer angeben (außer Kleinunternehmer)
            if not uid_requirements['seller_uid_required'] and uid_requirements['seller_tax_number_required']:
                if invoice.service_provider.company_uid:
                    dienstleister_info += f"<br/>USt-ID: {UIDValidator.format_uid_for_display(invoice.service_provider.company_uid)}"
                elif invoice.service_provider.company_tax_number:
                    dienstleister_info += f"<br/>Steuernummer: {UIDValidator.format_tax_number_for_display(invoice.service_provider.company_tax_number)}"
            elif uid_requirements['seller_uid_required']:
                if invoice.service_provider.company_uid:
                    dienstleister_info += f"<br/>USt-ID: {UIDValidator.format_uid_for_display(invoice.service_provider.company_uid)}"
                elif invoice.service_provider.company_tax_number:
                    dienstleister_info += f"<br/>Steuernummer: {UIDValidator.format_tax_number_for_display(invoice.service_provider.company_tax_number)}"
            
            if invoice.service_provider.email:
                dienstleister_info += f"<br/>{invoice.service_provider.email}"
            if invoice.service_provider.phone:
                dienstleister_info += f"<br/>{invoice.service_provider.phone}"
            story.append(Paragraph(dienstleister_info, styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Rechnungsdetails
            invoice_data = [
                ['Rechnungsnummer:', invoice.invoice_number],
                ['Rechnungsdatum:', invoice.invoice_date.strftime('%d.%m.%Y')],
                ['Fälligkeitsdatum:', invoice.due_date.strftime('%d.%m.%Y')],
                ['Projekt:', invoice.milestone.project.name],
                ['Gewerk:', invoice.milestone.title],
            ]
            
            if invoice.work_period_from and invoice.work_period_to:
                invoice_data.append(['Leistungszeitraum:', f"{invoice.work_period_from.strftime('%d.%m.%Y')} - {invoice.work_period_to.strftime('%d.%m.%Y')}"])
            
            # ✅ Flexible Kostenpositionen oder Legacy-Ansatz
            story.append(Paragraph("Leistungsverzeichnis", styles['Heading2']))
            story.append(Spacer(1, 10))
            
            # Lade Kostenpositionen wenn vorhanden
            cost_positions_data = [['Position', 'Betrag (EUR)']]
            
            if invoice.cost_positions:
                # ✅ Neue flexible Kostenpositionen
                for pos in invoice.cost_positions:
                    cost_positions_data.append([pos.description, f"{pos.amount:.2f}"])
            else:
                # Legacy: Verwende alte Kostenfelder falls vorhanden
                if invoice.material_costs and invoice.material_costs > 0:
                    cost_positions_data.append(['Materialkosten', f"{invoice.material_costs:.2f}"])
                if invoice.labor_costs and invoice.labor_costs > 0:
                    cost_positions_data.append(['Arbeitskosten', f"{invoice.labor_costs:.2f}"])
                if invoice.additional_costs and invoice.additional_costs > 0:
                    cost_positions_data.append(['Zusatzkosten', f"{invoice.additional_costs:.2f}"])
            
            # Zwischensumme und Gesamtbetrag
            cost_positions_data.extend([
                ['', ''],  # Leerzeile
                ['Nettobetrag', f"{invoice.net_amount:.2f}"],
                [f'MwSt. ({invoice.vat_rate:.0f}%)', f"{invoice.vat_amount:.2f}"],
                ['', ''],  # Leerzeile
                ['Gesamtbetrag', f"{invoice.total_amount:.2f}"]
            ])
            
            cost_table = Table(cost_positions_data, colWidths=[12*cm, 4*cm])
            cost_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Header fett
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Header-Hintergrund
                ('GRID', (0, 0), (-1, -2), 1, colors.black),  # Gitter bis vor Gesamtbetrag
                ('LINEBELOW', (0, -3), (-1, -3), 2, colors.black),  # Linie vor Gesamtbetrag
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),  # Gesamtbetrag fett
                ('FONTSIZE', (0, -1), (-1, -1), 12),  # Gesamtbetrag größer
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),  # Gesamtbetrag-Hintergrund
            ]))
            
            story.append(cost_table)
            story.append(Spacer(1, 20))
            
            # Beschreibung
            if invoice.description:
                story.append(Paragraph("Leistungsbeschreibung", styles['Heading3']))
                story.append(Paragraph(invoice.description, styles['Normal']))
                story.append(Spacer(1, 20))
            
            # Notizen
            if invoice.notes:
                story.append(Paragraph("Anmerkungen", styles['Heading3']))
                story.append(Paragraph(invoice.notes, styles['Normal']))
            
            # Erstelle PDF
            doc.build(story)
            
            print(f"✅ PDF generiert: {pdf_path}")
            
            # ✅ Automatische DMS-Integration
            await InvoiceService.create_dms_document(db, invoice, str(pdf_path))
            
            return str(pdf_path)
            
        except Exception as e:
            # Fallback: Erstelle einfache HTML-PDF mit weasyprint oder Text-Datei
            print(f"⚠️ PDF-Generierung mit ReportLab fehlgeschlagen: {e}")
            print("🔍 Versuche Fallback-PDF-Generierung...")
            
            try:
                # Erstelle einfache HTML-basierte PDF
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; }}
                        .header {{ text-align: center; margin-bottom: 30px; }}
                        .section {{ margin-bottom: 20px; }}
                        .table {{ width: 100%; border-collapse: collapse; }}
                        .table th, .table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                        .table th {{ background-color: #f2f2f2; }}
                        .total {{ font-weight: bold; }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>RECHNUNG {invoice.invoice_number}</h1>
                    </div>
                    
                    <div class="section">
                        <h3>Rechnungsempfänger:</h3>
                        <p>
                            {bautraeger.company_name if bautraeger and bautraeger.company_name else ''}<br/>
                            {bautraeger.first_name if bautraeger else ''} {bautraeger.last_name if bautraeger else ''}<br/>
                            {bautraeger.address_street if bautraeger and bautraeger.address_street else ''}<br/>
                            {f"{bautraeger.address_zip} {bautraeger.address_city}" if bautraeger and bautraeger.address_zip and bautraeger.address_city else (bautraeger.address_city if bautraeger and bautraeger.address_city else '')}<br/>
                            {bautraeger.address_country if bautraeger and bautraeger.address_country and bautraeger.address_country != "Deutschland" else ''}<br/>
                            {f"USt-ID: {UIDValidator.format_uid_for_display(bautraeger.company_uid)}" if bautraeger and bautraeger.company_uid and invoice.total_amount >= 10000.0 else ''}<br/>
                            {f"Steuernummer: {UIDValidator.format_tax_number_for_display(bautraeger.company_tax_number)}" if bautraeger and bautraeger.company_tax_number and invoice.total_amount >= 10000.0 and not bautraeger.company_uid else ''}<br/>
                            {bautraeger.email if bautraeger and bautraeger.email else ''}<br/>
                            {bautraeger.phone if bautraeger and bautraeger.phone else ''}
                        </p>
                    </div>
                    
                    <div class="section">
                        <h3>Rechnungssteller:</h3>
                        <p>
                            {invoice.service_provider.company_name if invoice.service_provider.company_name else ''}<br/>
                            {invoice.service_provider.first_name} {invoice.service_provider.last_name}<br/>
                            {invoice.service_provider.address_street if invoice.service_provider.address_street else ''}<br/>
                            {f"{invoice.service_provider.address_zip} {invoice.service_provider.address_city}" if invoice.service_provider.address_zip and invoice.service_provider.address_city else (invoice.service_provider.address_city if invoice.service_provider.address_city else '')}<br/>
                            {invoice.service_provider.address_country if invoice.service_provider.address_country and invoice.service_provider.address_country != "Deutschland" else ''}<br/>
                            {f"USt-ID: {UIDValidator.format_uid_for_display(invoice.service_provider.company_uid)}" if invoice.service_provider.company_uid else ''}<br/>
                            {f"Steuernummer: {UIDValidator.format_tax_number_for_display(invoice.service_provider.company_tax_number)}" if invoice.service_provider.company_tax_number and not invoice.service_provider.company_uid else ''}<br/>
                            {invoice.service_provider.email if invoice.service_provider.email else ''}<br/>
                            {invoice.service_provider.phone if invoice.service_provider.phone else ''}
                        </p>
                    </div>
                    
                    <div class="section">
                        <table class="table">
                            <tr><th>Rechnungsnummer</th><td>{invoice.invoice_number}</td></tr>
                            <tr><th>Rechnungsdatum</th><td>{invoice.invoice_date.strftime('%d.%m.%Y')}</td></tr>
                            <tr><th>Fälligkeitsdatum</th><td>{invoice.due_date.strftime('%d.%m.%Y')}</td></tr>
                            <tr><th>Projekt</th><td>{invoice.milestone.project.name}</td></tr>
                            <tr><th>Gewerk</th><td>{invoice.milestone.title}</td></tr>
                        </table>
                    </div>
                    
                    <div class="section">
                        <h3>Leistungsverzeichnis:</h3>
                        <table class="table">
                            <tr><th>Position</th><th>Betrag (EUR)</th></tr>
                """
                
                # Kostenpositionen hinzufügen
                if invoice.cost_positions:
                    for pos in invoice.cost_positions:
                        html_content += f"<tr><td>{pos.description}</td><td>{pos.amount:.2f}</td></tr>"
                else:
                    # Legacy-Kostenfelder
                    if invoice.material_costs and invoice.material_costs > 0:
                        html_content += f"<tr><td>Materialkosten</td><td>{invoice.material_costs:.2f}</td></tr>"
                    if invoice.labor_costs and invoice.labor_costs > 0:
                        html_content += f"<tr><td>Arbeitskosten</td><td>{invoice.labor_costs:.2f}</td></tr>"
                    if invoice.additional_costs and invoice.additional_costs > 0:
                        html_content += f"<tr><td>Zusatzkosten</td><td>{invoice.additional_costs:.2f}</td></tr>"
                
                html_content += f"""
                            <tr><td><strong>Nettobetrag</strong></td><td><strong>{invoice.net_amount:.2f}</strong></td></tr>
                            <tr><td>MwSt. ({invoice.vat_rate:.0f}%)</td><td>{invoice.vat_amount:.2f}</td></tr>
                            <tr class="total"><td><strong>Gesamtbetrag</strong></td><td><strong>{invoice.total_amount:.2f}</strong></td></tr>
                        </table>
                    </div>
                    
                    {f'<div class="section"><h3>Beschreibung:</h3><p>{invoice.description}</p></div>' if invoice.description else ''}
                </body>
                </html>
                """
                
                # Schreibe HTML-Datei
                html_path = pdf_path.with_suffix('.html')
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                print(f"✅ HTML-Fallback erstellt: {html_path}")
                return str(html_path)
                
            except Exception as fallback_error:
                print(f"❌ Auch HTML-Fallback fehlgeschlagen: {fallback_error}")
                # Letzter Fallback: Einfache Text-Datei
                with open(pdf_path.with_suffix('.txt'), 'w', encoding='utf-8') as f:
                    f.write(f"RECHNUNG {invoice.invoice_number}\n\n")
                    
                    if bautraeger:
                        f.write("RECHNUNGSEMPFÄNGER:\n")
                        if bautraeger.company_name:
                            f.write(f"{bautraeger.company_name}\n")
                        f.write(f"{bautraeger.first_name} {bautraeger.last_name}\n")
                        if bautraeger.address_street:
                            f.write(f"{bautraeger.address_street}\n")
                        if bautraeger.address_zip and bautraeger.address_city:
                            f.write(f"{bautraeger.address_zip} {bautraeger.address_city}\n")
                        elif bautraeger.address_city:
                            f.write(f"{bautraeger.address_city}\n")
                        if bautraeger.address_country and bautraeger.address_country != "Deutschland":
                            f.write(f"{bautraeger.address_country}\n")
                        if invoice.total_amount >= 10000.0:
                            if bautraeger.company_uid:
                                f.write(f"USt-ID: {UIDValidator.format_uid_for_display(bautraeger.company_uid)}\n")
                            elif bautraeger.company_tax_number:
                                f.write(f"Steuernummer: {UIDValidator.format_tax_number_for_display(bautraeger.company_tax_number)}\n")
                        if bautraeger.email:
                            f.write(f"{bautraeger.email}\n")
                        if bautraeger.phone:
                            f.write(f"{bautraeger.phone}\n")
                        f.write("\n")
                    
                    f.write("RECHNUNGSSTELLER:\n")
                    if invoice.service_provider.company_name:
                        f.write(f"{invoice.service_provider.company_name}\n")
                    f.write(f"{invoice.service_provider.first_name} {invoice.service_provider.last_name}\n")
                    if invoice.service_provider.address_street:
                        f.write(f"{invoice.service_provider.address_street}\n")
                    if invoice.service_provider.address_zip and invoice.service_provider.address_city:
                        f.write(f"{invoice.service_provider.address_zip} {invoice.service_provider.address_city}\n")
                    elif invoice.service_provider.address_city:
                        f.write(f"{invoice.service_provider.address_city}\n")
                    if invoice.service_provider.address_country and invoice.service_provider.address_country != "Deutschland":
                        f.write(f"{invoice.service_provider.address_country}\n")
                    if invoice.service_provider.company_uid:
                        f.write(f"USt-ID: {UIDValidator.format_uid_for_display(invoice.service_provider.company_uid)}\n")
                    elif invoice.service_provider.company_tax_number:
                        f.write(f"Steuernummer: {UIDValidator.format_tax_number_for_display(invoice.service_provider.company_tax_number)}\n")
                    if invoice.service_provider.email:
                        f.write(f"{invoice.service_provider.email}\n")
                    if invoice.service_provider.phone:
                        f.write(f"{invoice.service_provider.phone}\n")
                    f.write("\n")
                    
                    f.write(f"Rechnungsdatum: {invoice.invoice_date.strftime('%d.%m.%Y')}\n")
                    f.write(f"Fälligkeitsdatum: {invoice.due_date.strftime('%d.%m.%Y')}\n")
                    f.write(f"Projekt: {invoice.milestone.project.name}\n")
                    f.write(f"Gewerk: {invoice.milestone.title}\n\n")
                    
                    f.write("LEISTUNGSVERZEICHNIS:\n")
                    if invoice.cost_positions:
                        for pos in invoice.cost_positions:
                            f.write(f"- {pos.description}: {pos.amount:.2f} EUR\n")
                    else:
                        if invoice.material_costs and invoice.material_costs > 0:
                            f.write(f"- Materialkosten: {invoice.material_costs:.2f} EUR\n")
                        if invoice.labor_costs and invoice.labor_costs > 0:
                            f.write(f"- Arbeitskosten: {invoice.labor_costs:.2f} EUR\n")
                        if invoice.additional_costs and invoice.additional_costs > 0:
                            f.write(f"- Zusatzkosten: {invoice.additional_costs:.2f} EUR\n")
                    
                    f.write(f"\nNettobetrag: {invoice.net_amount:.2f} EUR\n")
                    f.write(f"MwSt. ({invoice.vat_rate:.0f}%): {invoice.vat_amount:.2f} EUR\n")
                    f.write(f"GESAMTBETRAG: {invoice.total_amount:.2f} EUR\n")
                    
                    if invoice.description:
                        f.write(f"\nBeschreibung: {invoice.description}\n")
                
                print(f"✅ Text-Fallback erstellt: {pdf_path.with_suffix('.txt')}")
                return str(pdf_path.with_suffix('.txt'))
    
    @staticmethod
    async def get_invoice_by_id(db: AsyncSession, invoice_id: int) -> Optional[Invoice]:
        """Hole eine Rechnung anhand der ID"""
        query = select(Invoice).where(Invoice.id == invoice_id).options(
            selectinload(Invoice.project),
            selectinload(Invoice.milestone).selectinload(Milestone.project),
            selectinload(Invoice.service_provider)
        )
        result = await db.execute(query)
        invoice = result.scalar_one_or_none()
        
        # Debug-Ausgabe für Problemdiagnose
        if invoice:
            print(f"🔍 Invoice {invoice_id} geladen:")
            print(f"  - project: {invoice.project}")
            print(f"  - milestone: {invoice.milestone}")
            print(f"  - milestone.project: {invoice.milestone.project if invoice.milestone else None}")
            print(f"  - service_provider: {invoice.service_provider}")
        
        return invoice
    
    @staticmethod
    async def get_invoices_for_project(
        db: AsyncSession, 
        project_id: int,
        status: Optional[InvoiceStatus] = None
    ) -> List[Invoice]:
        """Hole alle Rechnungen für ein Projekt"""
        query = select(Invoice).where(Invoice.project_id == project_id)
        
        if status:
            query = query.where(Invoice.status == status)
            
        query = query.options(
            selectinload(Invoice.milestone),
            selectinload(Invoice.service_provider)
        ).order_by(Invoice.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_invoices_for_service_provider(
        db: AsyncSession, 
        service_provider_id: int,
        status: Optional[InvoiceStatus] = None
    ) -> List[Invoice]:
        """Hole alle Rechnungen für einen Dienstleister"""
        query = select(Invoice).where(Invoice.service_provider_id == service_provider_id)
        
        if status:
            query = query.where(Invoice.status == status)
            
        query = query.options(
            selectinload(Invoice.project),
            selectinload(Invoice.milestone)
        ).order_by(Invoice.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_invoice_by_milestone(
        db: AsyncSession, 
        milestone_id: int
    ) -> Optional[Invoice]:
        """Hole die Rechnung für einen bestimmten Meilenstein (nur finale Rechnungen, keine Entwürfe)"""
        from ..models.invoice import InvoiceStatus
        
        # ✅ KRITISCH: Nur echte Rechnungen zurückgeben, keine DRAFT-Entwürfe!
        # DRAFT-Rechnungen werden automatisch beim Annehmen von Angeboten erstellt,
        # sollen aber erst angezeigt werden, wenn der Dienstleister sie finalisiert hat
        query = select(Invoice).where(
            Invoice.milestone_id == milestone_id,
            #Invoice.status != InvoiceStatus.DRAFT  # ✅ DRAFT-Status ausschließen
        ).options(
            selectinload(Invoice.project),
            selectinload(Invoice.service_provider)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def mark_invoice_as_paid(
        db: AsyncSession,
        invoice_id: int,
        payment_data: InvoicePayment
    ) -> Invoice:
        """Markiere eine Rechnung als bezahlt"""
        invoice = await InvoiceService.get_invoice_by_id(db, invoice_id)
        if not invoice:
            raise ValueError(f"Rechnung mit ID {invoice_id} nicht gefunden")
        
        old_status = invoice.status
        invoice.status = InvoiceStatus.PAID
        invoice.paid_at = payment_data.paid_at
        invoice.payment_reference = payment_data.payment_reference
        invoice.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(invoice)
        
        # ✅ Automatische DMS-Kategorisierung für bezahlte Rechnungen
        try:
            await InvoiceService.auto_categorize_paid_invoice(db, invoice)
            print(f"✅ DMS-Kategorisierung für bezahlte Rechnung {invoice.invoice_number} erfolgreich")
        except Exception as dms_error:
            print(f"⚠️ DMS-Kategorisierung nach Bezahlung fehlgeschlagen (nicht kritisch): {dms_error}")
            # DMS-Fehler sollen die Zahlungsmarkierung nicht blockieren
        
        print(f"✅ Rechnung {invoice.invoice_number} als bezahlt markiert")
        return invoice
    
    @staticmethod
    async def auto_categorize_paid_invoice(db: AsyncSession, invoice: Invoice) -> None:
        """Automatische DMS-Kategorisierung für bezahlte Rechnungen"""
        from ..schemas.document import DocumentCreate, DocumentCategory
        from ..utils.document_categorizer import DocumentCategorizer
        from ..services.document_service import DocumentService
        from pathlib import Path
        import os
        
        try:
            # Prüfe ob PDF-Datei existiert
            if not invoice.pdf_file_path or not Path(invoice.pdf_file_path).exists():
                print(f"⚠️ Keine PDF-Datei für Rechnung {invoice.invoice_number} gefunden")
                return
            
            # Lade Milestone und Service Provider für zusätzliche Informationen
            await db.refresh(invoice, ['milestone', 'service_provider', 'project'])
            
            # Generiere Dateiname und Metadaten
            filename = Path(invoice.pdf_file_path).name
            milestone_title = invoice.milestone.title if invoice.milestone else "Unbekanntes Gewerk"
            service_provider_name = invoice.service_provider.company_name if invoice.service_provider else "Unbekannt"
            
            # Automatische Kategorisierung mit DocumentCategorizer
            category = "finance"  # Fest auf Finanzen setzen
            subcategory = DocumentCategorizer.suggest_subcategory(
                category=category,
                filename=filename,
                invoice_status='paid',
                invoice_type=invoice.invoice_type or 'GENERATED'
            )
            
            # Generiere intelligente Tags
            tags = DocumentCategorizer.generate_tags(
                filename=filename,
                milestone_title=milestone_title,
                service_provider_name=service_provider_name,
                amount=float(invoice.amount),
                status='paid',
                invoice_type=invoice.invoice_type or 'GENERATED'
            )
            
            # Erstelle oder aktualisiere DMS-Dokument
            document_data = DocumentCreate(
                title=f"Bezahlte Rechnung - {invoice.invoice_number}",
                filename=filename,
                file_path=invoice.pdf_file_path,
                file_type="PDF",
                file_size=Path(invoice.pdf_file_path).stat().st_size,
                category=DocumentCategory.FINANCE,
                subcategory="Bezahlte Rechnungen",
                tags=tags,
                project_id=invoice.project_id,
                milestone_id=invoice.milestone_id,
                created_by_user_id=invoice.created_by_user_id,
                description=f"Automatisch kategorisierte bezahlte Rechnung von {service_provider_name} für {milestone_title}. Betrag: {invoice.amount}€"
            )
            
            # Prüfe ob bereits ein DMS-Dokument existiert
            if hasattr(invoice, 'dms_document_id') and invoice.dms_document_id:
                # Aktualisiere bestehendes Dokument
                await DocumentService.update_document(
                    db=db,
                    document_id=invoice.dms_document_id,
                    document_update=document_data
                )
                print(f"📁 DMS-Dokument {invoice.dms_document_id} für bezahlte Rechnung aktualisiert")
            else:
                # Erstelle neues DMS-Dokument
                document = await DocumentService.create_document(db=db, document=document_data)
                # Verknüpfe Rechnung mit DMS-Dokument (falls Feld existiert)
                if hasattr(invoice, 'dms_document_id'):
                    invoice.dms_document_id = document.id
                    await db.commit()
                print(f"📁 Neues DMS-Dokument {document.id} für bezahlte Rechnung erstellt")
            
            # Kopiere Datei in DMS-Storage-Struktur
            project_id = invoice.project_id
            target_dir = Path("storage") / "projects" / f"project_{project_id}" / "uploaded_documents" / "finance" / "bezahlte_rechnungen"
            target_dir.mkdir(parents=True, exist_ok=True)
            
            target_file = target_dir / filename
            if not target_file.exists():
                import shutil
                shutil.copy2(invoice.pdf_file_path, target_file)
                print(f"📄 Rechnung nach {target_file} kopiert")
            
        except Exception as e:
            print(f"❌ Fehler bei automatischer DMS-Kategorisierung: {e}")
            raise
    
    @staticmethod
    async def rate_service_provider(
        db: AsyncSession,
        invoice_id: int,
        rating_data: InvoiceRating,
        rated_by_user_id: int
    ) -> Invoice:
        """Bewerte den Dienstleister nach Rechnungsstellung"""
        invoice = await InvoiceService.get_invoice_by_id(db, invoice_id)
        if not invoice:
            raise ValueError(f"Rechnung mit ID {invoice_id} nicht gefunden")
        
        if invoice.status != InvoiceStatus.PAID:
            raise ValueError("Dienstleister kann nur nach Bezahlung der Rechnung bewertet werden")
        
        invoice.rating_quality = rating_data.rating_quality
        invoice.rating_timeliness = rating_data.rating_timeliness
        invoice.rating_overall = rating_data.rating_overall
        invoice.rating_notes = rating_data.rating_notes
        invoice.rated_by = rated_by_user_id
        invoice.rated_at = datetime.utcnow()
        invoice.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(invoice)
        
        print(f"✅ Dienstleister für Rechnung {invoice.invoice_number} bewertet")
        return invoice
    
    @staticmethod
    async def update_overdue_invoices(db: AsyncSession) -> int:
        """Aktualisiere überfällige Rechnungen"""
        current_date = datetime.utcnow()
        
        # Finde alle Rechnungen die überfällig sind
        overdue_query = select(Invoice).where(
            and_(
                Invoice.due_date < current_date,
                Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.VIEWED])
            )
        )
        result = await db.execute(overdue_query)
        overdue_invoices = result.scalars().all()
        
        count = 0
        for invoice in overdue_invoices:
            invoice.status = InvoiceStatus.OVERDUE
            invoice.updated_at = datetime.utcnow()
            count += 1
        
        if count > 0:
            await db.commit()
            print(f"✅ {count} Rechnungen als überfällig markiert")
        
        return count
    
    @staticmethod
    async def get_invoice_statistics(
        db: AsyncSession,
        project_id: Optional[int] = None,
        service_provider_id: Optional[int] = None
    ) -> InvoiceStats:
        """Hole Rechnungsstatistiken"""
        
        # Basis-Query
        query = select(Invoice)
        if project_id:
            query = query.where(Invoice.project_id == project_id)
        if service_provider_id:
            query = query.where(Invoice.service_provider_id == service_provider_id)
        
        result = await db.execute(query)
        invoices = result.scalars().all()
        
        if not invoices:
            return InvoiceStats()
        
        # Berechne Statistiken
        total_invoices = len(invoices)
        total_amount = sum(inv.total_amount for inv in invoices)
        paid_invoices = [inv for inv in invoices if inv.status == InvoiceStatus.PAID]
        paid_amount = sum(inv.total_amount for inv in paid_invoices)
        outstanding_amount = total_amount - paid_amount
        
        overdue_invoices = [
            inv for inv in invoices 
            if inv.status == InvoiceStatus.OVERDUE
        ]
        overdue_count = len(overdue_invoices)
        overdue_amount = sum(inv.total_amount for inv in overdue_invoices)
        
        # Berechne durchschnittliche Zahlungsdauer
        average_payment_days = None
        if paid_invoices:
            payment_days = []
            for inv in paid_invoices:
                if inv.paid_at and inv.invoice_date:
                    days = (inv.paid_at - inv.invoice_date).days
                    if days >= 0:  # Nur positive Werte
                        payment_days.append(days)
            
            if payment_days:
                average_payment_days = sum(payment_days) / len(payment_days)
        
        return InvoiceStats(
            total_invoices=total_invoices,
            total_amount=total_amount,
            paid_amount=paid_amount,
            outstanding_amount=outstanding_amount,
            overdue_count=overdue_count,
            overdue_amount=overdue_amount,
            average_payment_days=average_payment_days
        )
    
    @staticmethod
    async def create_dms_document(
        db: AsyncSession, 
        invoice: Invoice, 
        pdf_path: str,
        custom_subcategory: str = None
    ) -> None:
        """Erstelle automatisch ein DMS-Dokument für die Rechnung"""
        
        try:
            from ..services.document_service import create_document
            from ..schemas.document import DocumentCreate, DocumentTypeEnum, DocumentCategory
            from ..models.document import DocumentType
            
            # Bestimme den Dokumenttyp basierend auf Rechnungstyp
            if invoice.type == InvoiceType.MANUAL:
                document_type = DocumentType.INVOICE
            else:
                document_type = DocumentType.INVOICE
            
            # ✅ Automatische Kategorisierung mit DocumentCategorizer
            from ..utils.document_categorizer import DocumentCategorizer
            
            filename = f"Rechnung_{invoice.invoice_number}_{invoice.milestone.title}.pdf"
            category = DocumentCategorizer.categorize_document(filename, ".pdf")
            
            # Verwende custom_subcategory falls vorhanden, sonst automatische Erkennung
            if custom_subcategory:
                subcategory = custom_subcategory
            else:
                subcategory = DocumentCategorizer.suggest_subcategory(
                    category, 
                    filename, 
                    invoice.status.value, 
                    invoice.type.value if invoice.type else None
                )
            
            # Intelligente Tag-Generierung
            tags = DocumentCategorizer.generate_tags(
                filename=filename,
                milestone_title=invoice.milestone.title,
                service_provider_name=invoice.service_provider.company_name or invoice.service_provider.last_name,
                amount=float(invoice.total_amount),
                status=invoice.status.value,
                invoice_type=invoice.type.value if invoice.type else "UNKNOWN"
            )
            
            # Erstelle DMS-Dokument mit intelligenter Kategorisierung
            document_data = DocumentCreate(
                project_id=invoice.project_id,
                title=f"Rechnung {invoice.invoice_number} - {invoice.milestone.title}",
                description=f"Rechnung für Gewerk: {invoice.milestone.title}\n"
                           f"Dienstleister: {invoice.service_provider.first_name} {invoice.service_provider.last_name}\n"
                           f"Betrag: {invoice.total_amount:.2f} EUR\n"
                           f"Status: {invoice.status.value}\n"
                           f"Automatisch kategorisiert als: {subcategory}",
                document_type=DocumentTypeEnum.INVOICE,
                category=DocumentCategory.FINANCE,  # Rechnungen bleiben in FINANCE-Kategorie
                subcategory=subcategory,
                file_name=f"Rechnung_{invoice.invoice_number}_{invoice.id}.pdf",
                file_path=pdf_path,
                file_size=Path(pdf_path).stat().st_size if Path(pdf_path).exists() else 0,
                mime_type="application/pdf",
                tags=tags,
                is_public=False,  # Rechnungen sind nicht öffentlich
                version_number="1.0.0"
            )
            
            # Erstelle das DMS-Dokument
            dms_document = await create_document(
                db=db,
                document_in=document_data,
                uploaded_by=invoice.created_by
            )
            
            print(f"✅ DMS-Dokument erstellt: {dms_document.title} (ID: {dms_document.id})")
            
            # Aktualisiere die Rechnung mit der DMS-Referenz
            invoice.dms_document_id = dms_document.id
            # Speichere auch den Pfad zum Dokument, um das Dokument im DMS Verzeichnis zu finden
            if not dms_document.file_path.startswith("storage/documents/"):
                # Erstelle eine Kopie des Dokuments im DMS Verzeichnis
                import shutil
                os.makedirs("storage/documents", exist_ok=True)
                dms_dest_path = f"storage/documents/Rechnung_{invoice.invoice_number}_{invoice.id}.pdf"
                shutil.copy(pdf_path, dms_dest_path)
                # Aktualisiere den Pfad des DMS-Dokuments
                dms_document.file_path = dms_dest_path
            await db.commit()
            
        except Exception as e:
            print(f"❌ Fehler bei DMS-Integration: {e}")
            # Fehler bei DMS-Integration sollte nicht die Rechnungserstellung blockieren
    
    @staticmethod
    async def update_dms_document_for_payment(
        db: AsyncSession,
        invoice: Invoice
    ) -> None:
        """Aktualisiert ein DMS-Dokument nach Zahlungseingang"""
        
        try:
            # Einfache DMS-Update-Logik ohne komplexe Abhängigkeiten
            print(f"🔍 Versuche DMS-Update für Rechnung {invoice.invoice_number}")
            
            # Prüfe ob alle erforderlichen Services verfügbar sind
            try:
                from ..services.document_service import update_document
                from ..schemas.document import DocumentUpdate
            except ImportError as import_error:
                print(f"⚠️ DMS-Services nicht verfügbar: {import_error}")
                return
            
            # Einfache Update-Daten ohne DocumentCategorizer
            update_data = DocumentUpdate(
                title=f"Rechnung {invoice.invoice_number} - {invoice.milestone.title} (BEZAHLT)",
                description=f"Rechnung für Gewerk: {invoice.milestone.title}\n"
                           f"Dienstleister: {invoice.service_provider.first_name} {invoice.service_provider.last_name}\n"
                           f"Betrag: {invoice.total_amount:.2f} EUR\n"
                           f"Status: BEZAHLT am {invoice.paid_at.strftime('%d.%m.%Y') if invoice.paid_at else 'Unbekannt'}",
                subcategory="Bezahlte Rechnungen",
                tags=["Rechnung", "Bezahlt", "Finanzen", invoice.milestone.title]
            )
            
            # Führe das Update durch
            await update_document(
                db=db,
                document_id=getattr(invoice, 'dms_document_id', None),
                document_in=update_data,
                updated_by=getattr(invoice, 'created_by', None)
            )
            
            print(f"✅ DMS-Dokument für bezahlte Rechnung {invoice.invoice_number} aktualisiert")
            
        except Exception as e:
            print(f"❌ Fehler beim DMS-Update: {e}")
            import traceback
            print(f"🔍 DMS-Update Traceback: {traceback.format_exc()}")
            # Fehler beim DMS-Update sollte nicht die Zahlungsmarkierung blockieren