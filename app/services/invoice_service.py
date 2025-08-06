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
        
        # ✅ Automatische DMS-Integration für manuelle Rechnungen
        # PDF wird erst beim ersten Download generiert
        print(f"✅ Manuelle Rechnung erstellt: {invoice.invoice_number} für Meilenstein {milestone.title}")
        
        # Debug: Prüfe Invoice-Objekt
        print(f"🔍 Invoice ID: {invoice.id}")
        print(f"🔍 Invoice Number: {invoice.invoice_number}")
        print(f"🔍 Invoice Status: {invoice.status}")
        print(f"🔍 Invoice Type: {invoice.type}")
        print(f"🔍 Invoice Date: {invoice.invoice_date}")
        print(f"🔍 Invoice Due Date: {invoice.due_date}")
        
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
        
        # Speichere die PDF-Datei
        upload_dir = Path("storage/invoices")
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
            selectinload(Invoice.milestone).selectinload(Milestone.project),
            selectinload(Invoice.service_provider),
            selectinload(Invoice.cost_positions)  # ✅ Lade auch die Kostenpositionen
        ).where(Invoice.id == invoice_id)
        
        result = await db.execute(invoice_query)
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            raise ValueError(f"Rechnung mit ID {invoice_id} nicht gefunden")
        
        # Erstelle PDF-Verzeichnis
        pdf_dir = Path("storage/invoices")
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
            
            # Rechnungsdetails
            invoice_data = [
                ['Rechnungsnummer:', invoice.invoice_number],
                ['Rechnungsdatum:', invoice.invoice_date.strftime('%d.%m.%Y')],
                ['Fälligkeitsdatum:', invoice.due_date.strftime('%d.%m.%Y')],
                ['Projekt:', invoice.milestone.project.name],
                ['Gewerk:', invoice.milestone.title],
                ['Dienstleister:', f"{invoice.service_provider.first_name} {invoice.service_provider.last_name}"],
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
            
        except ImportError:
            # Fallback: Erstelle einfache Text-PDF
            print("⚠️ ReportLab nicht verfügbar, erstelle einfache PDF")
            
            with open(pdf_path, 'w') as f:
                f.write(f"RECHNUNG {invoice.invoice_number}\n")
                f.write(f"Rechnungsdatum: {invoice.invoice_date.strftime('%d.%m.%Y')}\n")
                f.write(f"Fälligkeitsdatum: {invoice.due_date.strftime('%d.%m.%Y')}\n")
                f.write(f"Projekt: {invoice.milestone.project.name}\n")
                f.write(f"Gewerk: {invoice.milestone.title}\n")
                f.write(f"Dienstleister: {invoice.service_provider.first_name} {invoice.service_provider.last_name}\n")
                f.write(f"Nettobetrag: {invoice.net_amount:.2f} EUR\n")
                f.write(f"MwSt. ({invoice.vat_rate:.0f}%): {invoice.vat_amount:.2f} EUR\n")
                f.write(f"Gesamtbetrag: {invoice.total_amount:.2f} EUR\n")
                if invoice.description:
                    f.write(f"Beschreibung: {invoice.description}\n")
            
            return str(pdf_path)
    
    @staticmethod
    async def get_invoice_by_id(db: AsyncSession, invoice_id: int) -> Optional[Invoice]:
        """Hole eine Rechnung anhand der ID"""
        query = select(Invoice).where(Invoice.id == invoice_id).options(
            selectinload(Invoice.project),
            selectinload(Invoice.milestone),
            selectinload(Invoice.service_provider)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
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
        """Hole die Rechnung für einen bestimmten Meilenstein"""
        query = select(Invoice).where(Invoice.milestone_id == milestone_id).options(
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
        
        invoice.status = InvoiceStatus.PAID
        invoice.paid_at = payment_data.paid_at
        invoice.payment_reference = payment_data.payment_reference
        invoice.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(invoice)
        
        print(f"✅ Rechnung {invoice.invoice_number} als bezahlt markiert")
        return invoice
    
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
        pdf_path: str
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
            
            # Erstelle DMS-Dokument
            document_data = DocumentCreate(
                project_id=invoice.project_id,
                title=f"Rechnung {invoice.invoice_number} - {invoice.milestone.title}",
                description=f"Rechnung für Gewerk: {invoice.milestone.title}\n"
                           f"Dienstleister: {invoice.service_provider.first_name} {invoice.service_provider.last_name}\n"
                           f"Betrag: {invoice.total_amount:.2f} EUR\n"
                           f"Status: {invoice.status.value}",
                document_type=DocumentTypeEnum.INVOICE,
                category=DocumentCategory.FINANCE,
                subcategory="Rechnungen",
                file_name=f"Rechnung_{invoice.invoice_number}_{invoice.id}.pdf",
                file_path=pdf_path,
                file_size=Path(pdf_path).stat().st_size if Path(pdf_path).exists() else 0,
                mime_type="application/pdf",
                tags=["Rechnung", "Finanzen", invoice.milestone.title],
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