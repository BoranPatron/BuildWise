import os
from datetime import date, timedelta, datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, extract, select
from sqlalchemy.exc import IntegrityError

from app.models.buildwise_fee import BuildWiseFee, BuildWiseFeeItem, BuildWiseFeeStatus
from app.models.quote import Quote
from app.models.cost_position import CostPosition
from app.models.project import Project
from app.schemas.buildwise_fee import (
    BuildWiseFeeCreate, 
    BuildWiseFeeUpdate, 
    BuildWiseFeeItemCreate,
    BuildWiseFeeStatistics
)
from app.core.config import settings, get_fee_percentage
from app.services.pdf_generator import BuildWisePDFGenerator

class BuildWiseFeeService:
    
    @staticmethod
    async def create_fee_from_quote(
        db: AsyncSession, 
        quote_id: int, 
        cost_position_id: int, 
        fee_percentage: Optional[float] = None
    ) -> BuildWiseFee:
        """Erstellt automatisch eine BuildWise-Gebühr aus einem akzeptierten Angebot."""
        
        # Hole das Angebot mit allen notwendigen Informationen
        quote_query = select(Quote).where(Quote.id == quote_id)
        quote_result = await db.execute(quote_query)
        quote = quote_result.scalar_one_or_none()
        
        if not quote:
            raise ValueError(f"Angebot mit ID {quote_id} nicht gefunden")
        
        # Prüfe ob bereits eine Gebühr für dieses Angebot existiert
        existing_fee_query = select(BuildWiseFee).where(BuildWiseFee.quote_id == quote_id)
        existing_fee_result = await db.execute(existing_fee_query)
        existing_fee = existing_fee_result.scalar_one_or_none()
        
        if existing_fee:
            raise ValueError(f"Für Angebot {quote_id} existiert bereits eine Gebühr")
        
        # Verwende den aktuellen Gebühren-Prozentsatz aus der Konfiguration
        if fee_percentage is None:
            fee_percentage = get_fee_percentage()
        
        # Berechne die Gebühr
        quote_amount = float(quote.total_amount)
        fee_amount = quote_amount * (fee_percentage / 100.0)
        
        # Generiere Rechnungsnummer
        last_fee_query = select(BuildWiseFee).order_by(BuildWiseFee.id.desc()).limit(1)
        last_fee_result = await db.execute(last_fee_query)
        last_fee = last_fee_result.scalar_one_or_none()
        
        if last_fee and last_fee.invoice_number:
            # Extrahiere Nummer aus letzter Rechnung
            try:
                last_number = int(last_fee.invoice_number.split('-')[-1])
                invoice_number = f"BW-{last_number + 1:06d}"
            except:
                invoice_number = "BW-000001"
        else:
            invoice_number = "BW-000001"
        
        # Erstelle die Gebühr
        fee_data = BuildWiseFeeCreate(
            project_id=int(quote.project_id),
            quote_id=quote_id,
            cost_position_id=cost_position_id,
            service_provider_id=int(quote.service_provider_id),
            fee_amount=Decimal(str(fee_amount)),
            fee_percentage=Decimal(str(fee_percentage)),
            quote_amount=Decimal(str(quote_amount)),
            currency=str(quote.currency),
            invoice_number=invoice_number,
            invoice_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            status='open',
            invoice_pdf_generated=False,
            tax_rate=Decimal("19.0"),
            tax_amount=Decimal(str(fee_amount * 0.19)),
            net_amount=Decimal(str(fee_amount)),
            gross_amount=Decimal(str(fee_amount * 1.19)),
            fee_details=f"BuildWise-Gebühr für akzeptiertes Angebot {quote_id}",
            notes=f"Automatisch generiert bei Angebotsannahme"
        )
        
        # Erstelle das BuildWiseFee-Objekt
        fee = BuildWiseFee(**fee_data.dict())
        db.add(fee)
        await db.commit()
        await db.refresh(fee)
        
        return fee
    
    @staticmethod
    async def get_fees(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> List[BuildWiseFee]:
        """Holt BuildWise-Gebühren mit optionalen Filtern."""
        
        try:
            print(f"🔍 Debug: BuildWiseFeeService.get_fees aufgerufen mit: skip={skip}, limit={limit}, project_id={project_id}, status={status}, month={month}, year={year}")
            
            # Robuste Prüfung: Prüfe ob Tabelle existiert und Daten hat
            try:
                # Zuerst: Prüfe alle Datensätze ohne Filter
                all_fees_query = select(BuildWiseFee)
                all_result = await db.execute(all_fees_query)
                all_fees = all_result.scalars().all()
                print(f"🔍 Debug: Gesamtanzahl Datensätze in DB: {len(all_fees)}")
                
                # Wenn keine Daten vorhanden sind, gib leere Liste zurück
                if len(all_fees) == 0:
                    print("⚠️ Debug: Keine Datensätze in buildwise_fees Tabelle gefunden")
                    print("💡 Tipp: Führen Sie ensure_buildwise_fees_data.py aus")
                    return []
                
                # Zeige alle Datensätze für Debug
                for i, fee in enumerate(all_fees):
                    print(f"  Datensatz {i+1}: ID={fee.id}, Project={fee.project_id}, Status={fee.status}, Amount={fee.fee_amount}")
                    
            except Exception as table_error:
                print(f"⚠️ Debug: Fehler beim Zugriff auf buildwise_fees Tabelle: {table_error}")
                print("💡 Tipp: Prüfen Sie die Datenbank-Migrationen")
                return []
            
            # Hauptquery mit Filtern
            query = select(BuildWiseFee)
            
            # Filter anwenden
            if project_id:
                query = query.where(BuildWiseFee.project_id == project_id)
                print(f"🔍 Debug: Filter für project_id={project_id} angewendet")
            
            if status:
                query = query.where(BuildWiseFee.status == status)
                print(f"🔍 Debug: Filter für status={status} angewendet")
            
            # Datum-Filter - nur anwenden wenn beide Parameter vorhanden sind
            if month and year:
                # Verwende created_at für Datum-Filter
                start_date = datetime(year, month, 1)
                if month == 12:
                    end_date = datetime(year + 1, 1, 1)
                else:
                    end_date = datetime(year, month + 1, 1)
                
                # Verwende OR-Bedingung: entweder im Datumsbereich ODER kein Datum gesetzt
                from sqlalchemy import or_
                query = query.where(
                    or_(
                        (BuildWiseFee.created_at >= start_date) & (BuildWiseFee.created_at < end_date),
                        BuildWiseFee.created_at.is_(None)
                    )
                )
                print(f"🔍 Debug: Datum-Filter angewendet: {start_date} bis {end_date} (inkl. NULL-Werte)")
            
            # Pagination
            query = query.offset(skip).limit(limit)
            
            print("🔍 Debug: Führe gefilterte Query aus...")
            result = await db.execute(query)
            fees = result.scalars().all()
            
            print(f"✅ Debug: {len(fees)} Gebühren nach Filterung gefunden")
            
            # Zeige gefilterte Datensätze für Debug
            for i, fee in enumerate(fees):
                print(f"  Gefilterter Datensatz {i+1}: ID={fee.id}, Project={fee.project_id}, Status={fee.status}, Amount={fee.fee_amount}")
            
            # Konvertiere zu Liste
            fees_list = list(fees)
            print(f"✅ Debug: {len(fees_list)} Gebühren erfolgreich geladen")
            return fees_list
            
        except Exception as e:
            print(f"❌ Debug: Fehler in get_fees: {str(e)}")
            import traceback
            traceback.print_exc()
            # Bei Fehlern gib leere Liste zurück statt Exception zu werfen
            print("⚠️ Debug: Gebe leere Liste zurück bei Fehler")
            return []
    
    @staticmethod
    async def get_fee(db: AsyncSession, fee_id: int) -> Optional[BuildWiseFee]:
        """Holt eine spezifische BuildWise-Gebühr."""
        
        query = select(BuildWiseFee).where(BuildWiseFee.id == fee_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_fee(
        db: AsyncSession, 
        fee_id: int, 
        fee_data: BuildWiseFeeUpdate
    ) -> Optional[BuildWiseFee]:
        """Aktualisiert eine BuildWise-Gebühr."""
        
        query = select(BuildWiseFee).where(BuildWiseFee.id == fee_id)
        result = await db.execute(query)
        fee = result.scalar_one_or_none()
        
        if not fee:
            return None
        
        # Aktualisiere die Felder
        update_data = fee_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(fee, field, value)
        
        await db.commit()
        await db.refresh(fee)
        return fee
    
    @staticmethod
    async def mark_as_paid(
        db: AsyncSession, 
        fee_id: int, 
        payment_date: Optional[date] = None
    ) -> Optional[BuildWiseFee]:
        """Markiert eine Gebühr als bezahlt."""
        
        query = select(BuildWiseFee).where(BuildWiseFee.id == fee_id)
        result = await db.execute(query)
        fee = result.scalar_one_or_none()
        
        if not fee:
            return None
        
        fee.status = 'paid'
        if payment_date:
            fee.payment_date = payment_date.isoformat()
        else:
            fee.payment_date = date.today().isoformat()
        
        await db.commit()
        await db.refresh(fee)
        return fee
    
    @staticmethod
    async def get_statistics(db: AsyncSession) -> BuildWiseFeeStatistics:
        """Holt Statistiken für BuildWise-Gebühren."""
        
        # Gesamtanzahl
        total_fees_query = select(func.count(BuildWiseFee.id))
        total_fees_result = await db.execute(total_fees_query)
        total_fees = total_fees_result.scalar()
        
        # Gesamtbetrag
        total_amount_query = select(func.sum(BuildWiseFee.fee_amount))
        total_amount_result = await db.execute(total_amount_query)
        total_amount = total_amount_result.scalar() or 0.0
        
        # Bezahlte Gebühren
        paid_query = select(func.sum(BuildWiseFee.fee_amount)).where(BuildWiseFee.status == 'paid')
        paid_result = await db.execute(paid_query)
        total_paid = paid_result.scalar() or 0.0
        
        # Offene Gebühren
        open_query = select(func.sum(BuildWiseFee.fee_amount)).where(BuildWiseFee.status == 'open')
        open_result = await db.execute(open_query)
        total_open = open_result.scalar() or 0.0
        
        # Überfällige Gebühren
        overdue_query = select(func.sum(BuildWiseFee.fee_amount)).where(BuildWiseFee.status == 'overdue')
        overdue_result = await db.execute(overdue_query)
        total_overdue = overdue_result.scalar() or 0.0
        
        # Monatliche Aufschlüsselung
        monthly_query = select(
            extract('month', BuildWiseFee.invoice_date).label('month'),
            extract('year', BuildWiseFee.invoice_date).label('year'),
            func.sum(BuildWiseFee.fee_amount).label('amount'),
            func.count(BuildWiseFee.id).label('count')
        ).group_by(
            extract('month', BuildWiseFee.invoice_date),
            extract('year', BuildWiseFee.invoice_date)
        ).order_by(
            extract('year', BuildWiseFee.invoice_date).desc(),
            extract('month', BuildWiseFee.invoice_date).desc()
        ).limit(12)
        
        monthly_result = await db.execute(monthly_query)
        monthly_breakdown = []
        for row in monthly_result:
            if row.month is not None and row.year is not None:
                monthly_breakdown.append({
                    'month': int(row.month),
                    'year': int(row.year),
                    'amount': float(row.amount or 0),
                    'count': int(row.count or 0)
                })
        
        # Status-Aufschlüsselung
        status_query = select(
            BuildWiseFee.status,
            func.count(BuildWiseFee.id).label('count'),
            func.sum(BuildWiseFee.fee_amount).label('amount')
        ).group_by(BuildWiseFee.status)
        
        status_result = await db.execute(status_query)
        status_breakdown = {}
        for row in status_result:
            status_breakdown[row.status] = {
                'count': int(row.count),
                'amount': float(row.amount)
            }
        
        return BuildWiseFeeStatistics(
            total_fees=total_fees,
            total_amount=float(total_amount),
            total_paid=float(total_paid),
            total_open=float(total_open),
            total_overdue=float(total_overdue),
            monthly_breakdown=monthly_breakdown,
            status_breakdown=status_breakdown
        )
    
    @staticmethod
    async def generate_invoice(db: AsyncSession, fee_id: int) -> bool:
        """Generiert eine PDF-Rechnung für eine Gebühr."""
        
        query = select(BuildWiseFee).where(BuildWiseFee.id == fee_id)
        result = await db.execute(query)
        fee = result.scalar_one_or_none()
        
        if not fee:
            return False
        
        try:
            # Hole alle notwendigen Daten
            # Projekt
            project_query = select(Project).where(Project.id == fee.project_id)
            project_result = await db.execute(project_query)
            project = project_result.scalar_one_or_none()
            
            # Angebot
            quote_query = select(Quote).where(Quote.id == fee.quote_id)
            quote_result = await db.execute(quote_query)
            quote = quote_result.scalar_one_or_none()
            
            # Kostenposition
            cost_position_query = select(CostPosition).where(CostPosition.id == fee.cost_position_id)
            cost_position_result = await db.execute(cost_position_query)
            cost_position = cost_position_result.scalar_one_or_none()
            
            if not project or not quote or not cost_position:
                return False
            
            # Erstelle PDF-Generator
            pdf_generator = BuildWisePDFGenerator()
            
            # Erstelle Ausgabepfad
            invoices_dir = "storage/invoices"
            os.makedirs(invoices_dir, exist_ok=True)
            output_path = f"{invoices_dir}/buildwise_fee_{fee_id}.pdf"
            
            # Konvertiere SQLAlchemy-Objekte zu Dictionaries
            fee_data = {
                'id': fee.id,
                'invoice_number': fee.invoice_number,
                'invoice_date': fee.invoice_date,
                'due_date': fee.due_date,
                'status': fee.status,
                'fee_amount': float(fee.fee_amount),
                'fee_percentage': float(fee.fee_percentage),
                'tax_rate': float(fee.tax_rate),
                'notes': fee.notes
            }
            
            project_data = {
                'id': project.id,
                'name': project.name,
                'project_type': project.project_type,
                'status': project.status,
                'budget': float(project.budget) if project.budget else 0,
                'address': project.address
            }
            
            quote_data = {
                'id': quote.id,
                'title': quote.title,
                'total_amount': float(quote.total_amount),
                'currency': quote.currency,
                'valid_until': quote.valid_until,
                'company_name': quote.company_name,
                'contact_person': quote.contact_person,
                'email': quote.email,
                'phone': quote.phone
            }
            
            cost_position_data = {
                'title': cost_position.title,
                'description': cost_position.description,
                'amount': float(cost_position.amount),
                'category': cost_position.category,
                'status': cost_position.status,
                'contractor_name': cost_position.contractor_name
            }
            
            # Generiere PDF
            success = pdf_generator.generate_invoice_pdf(
                fee_data=fee_data,
                project_data=project_data,
                quote_data=quote_data,
                cost_position_data=cost_position_data,
                output_path=output_path
            )
            
            if success:
                # Aktualisiere Gebühr
                fee.invoice_pdf_generated = True
                fee.invoice_pdf_path = output_path
                await db.commit()
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Fehler beim Generieren der PDF: {e}")
            return False
    
    @staticmethod
    async def delete_fee(db: AsyncSession, fee_id: int) -> bool:
        """Löscht eine BuildWise-Gebühr."""
        
        query = select(BuildWiseFee).where(BuildWiseFee.id == fee_id)
        result = await db.execute(query)
        fee = result.scalar_one_or_none()
        
        if not fee:
            return False
        
        await db.delete(fee)
        await db.commit()
        return True
    
    @staticmethod
    async def check_overdue_fees(db: AsyncSession) -> dict:
        """Prüft auf überfällige Gebühren."""
        
        today = date.today()
        overdue_query = select(BuildWiseFee).where(
            and_(
                BuildWiseFee.status == 'open',
                BuildWiseFee.due_date < today.isoformat()
            )
        )
        
        overdue_result = await db.execute(overdue_query)
        overdue_fees = overdue_result.scalars().all()
        
        # Markiere als überfällig
        for fee in overdue_fees:
            fee.status = 'overdue'
        
        await db.commit()
        
        return {
            "message": f"{len(overdue_fees)} Gebühren als überfällig markiert",
            "overdue_count": len(overdue_fees)
        } 