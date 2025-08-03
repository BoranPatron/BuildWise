"""
Invoice service for construction billing and payment management
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import os
import uuid
from pathlib import Path

from app.models import (
    Invoice, InvoiceStatus, InvoiceType, 
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
        
        if existing_invoice:
            raise ValueError(f"Für Meilenstein {invoice_data.milestone_id} existiert bereits eine Rechnung")
        
        # Erstelle die Rechnung
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
        await db.commit()
        await db.refresh(invoice)
        
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
        
        if existing_invoice:
            raise ValueError(f"Für Meilenstein {invoice_data.milestone_id} existiert bereits eine Rechnung")
        
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
        
        # Erstelle die Rechnung
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
        
        db.add(invoice)
        await db.commit()
        await db.refresh(invoice)
        
        print(f"✅ PDF-Rechnung hochgeladen: {invoice.invoice_number} für Meilenstein {milestone.title}")
        return invoice
    
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