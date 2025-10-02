import os
from datetime import date, timedelta, datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, or_, extract, select
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
        """
        Erstellt automatisch eine BuildWise-Gebühr aus einem akzeptierten Angebot.
        
        Die Gebühr wird mit folgenden Parametern erstellt:
        - Provisionssatz: 4.7% (konfigurierbar via environment_mode)
        - Fälligkeitsdatum: +30 Tage ab Rechnungsdatum
        - Status: 'open' (offen)
        
        Args:
            db: Datenbank-Session
            quote_id: ID des akzeptierten Angebots
            cost_position_id: ID der zugehörigen Kostenposition
            fee_percentage: Optionaler Prozentsatz (Standard: aus Konfiguration)
            
        Returns:
            BuildWiseFee: Die erstellte Gebühr
            
        Raises:
            ValueError: Wenn das Angebot nicht gefunden wird oder bereits eine Gebühr existiert
        """
        
        print(f"[BuildWiseFeeService] Erstelle Gebuehr fuer Quote {quote_id}")
        
        # Hole das Angebot mit allen notwendigen Informationen
        quote_query = select(Quote).where(Quote.id == quote_id)
        quote_result = await db.execute(quote_query)
        quote = quote_result.scalar_one_or_none()
        
        if not quote:
            error_msg = f"Angebot mit ID {quote_id} nicht gefunden"
            print(f"[BuildWiseFeeService] {error_msg}")
            raise ValueError(error_msg)
        
        # Validiere dass das Angebot akzeptiert wurde
        quote_status = str(quote.status.value).upper() if hasattr(quote.status, 'value') else str(quote.status).upper()
        if quote_status != 'ACCEPTED':
            error_msg = f"Angebot {quote_id} ist nicht akzeptiert (Status: {quote_status})"
            print(f"[BuildWiseFeeService] {error_msg}")
            raise ValueError(error_msg)
        
        # Prüfe ob bereits eine Gebühr für dieses Angebot existiert
        existing_fee_query = select(BuildWiseFee).where(BuildWiseFee.quote_id == quote_id)
        existing_fee_result = await db.execute(existing_fee_query)
        existing_fee = existing_fee_result.scalar_one_or_none()
        
        if existing_fee:
            print(f"[BuildWiseFeeService] Gebuehr fuer Quote {quote_id} existiert bereits (ID: {existing_fee.id})")
            print(f"   - Status: {existing_fee.status}")
            print(f"   - Betrag: {existing_fee.fee_amount} {existing_fee.currency}")
            print(f"   - Rechnungsnummer: {existing_fee.invoice_number}")
            return existing_fee  # Gebe existierende Gebühr zurück statt Fehler
        
        # Verwende den aktuellen Gebühren-Prozentsatz aus der Konfiguration
        # Standard: 4.7% in Production, 0% in Beta
        if fee_percentage is None:
            fee_percentage = get_fee_percentage()
        
        print(f"[BuildWiseFeeService] Verwende Provisionssatz: {fee_percentage}%")
        
        # Validiere Quote-Daten
        if not quote.total_amount or quote.total_amount <= 0:
            error_msg = f"Ungültiger Quote-Betrag: {quote.total_amount}"
            print(f"[BuildWiseFeeService] {error_msg}")
            raise ValueError(error_msg)
        
        if not quote.project_id:
            error_msg = f"Quote {quote_id} hat keine gültige project_id"
            print(f"[BuildWiseFeeService] {error_msg}")
            raise ValueError(error_msg)
        
        if not quote.service_provider_id:
            error_msg = f"Quote {quote_id} hat keine gültige service_provider_id"
            print(f"[BuildWiseFeeService] {error_msg}")
            raise ValueError(error_msg)
        
        # Berechne die Gebühr
        quote_amount = float(quote.total_amount)
        fee_amount_raw = quote_amount * (fee_percentage / 100.0)
        
        # WICHTIG: Runde auf 2 Dezimalstellen, um Pydantic-Validierungsfehler zu vermeiden
        fee_amount = round(fee_amount_raw, 2)
        
        # Validierung: Gebühr darf nicht negativ sein
        if fee_amount < 0:
            error_msg = f"Gebührenbetrag ist negativ: {fee_amount}"
            print(f"[BuildWiseFeeService] {error_msg}")
            raise ValueError(error_msg)
        
        # Validierung: Minimaler Gebührenbetrag (z.B. 0.01 EUR)
        if fee_amount > 0 and fee_amount < 0.01:
            print(f"[BuildWiseFeeService] Gebuehrenbetrag sehr klein: {fee_amount}, setze auf 0.01")
            fee_amount = 0.01
        
        # Generiere Rechnungsnummer (Format: BW-XXXXXX) - Robuste Implementierung
        invoice_number = "BW-000001"  # Fallback
        try:
            # Suche nach der höchsten existierenden Rechnungsnummer
            last_fee_query = select(BuildWiseFee).where(
                BuildWiseFee.invoice_number.like('BW-%')
            ).order_by(BuildWiseFee.invoice_number.desc()).limit(1)
            last_fee_result = await db.execute(last_fee_query)
            last_fee = last_fee_result.scalar_one_or_none()
            
            if last_fee and last_fee.invoice_number:
                # Extrahiere Nummer aus letzter Rechnung
                try:
                    # Format: BW-123456
                    number_part = last_fee.invoice_number.split('-')[-1]
                    last_number = int(number_part)
                    invoice_number = f"BW-{last_number + 1:06d}"
                    print(f"[BuildWiseFeeService] Naechste Rechnungsnummer: {invoice_number} (basierend auf {last_fee.invoice_number})")
                except (ValueError, IndexError) as e:
                    print(f"[BuildWiseFeeService] Fehler beim Parsen der letzten Rechnungsnummer '{last_fee.invoice_number}': {e}")
                    # Fallback: Verwende aktuelle Zeit für Eindeutigkeit
                    import time
                    timestamp_suffix = int(time.time()) % 1000000
                    invoice_number = f"BW-{timestamp_suffix:06d}"
            else:
                print(f"[BuildWiseFeeService] Keine vorherige Rechnung gefunden, starte mit: {invoice_number}")
                
        except Exception as e:
            print(f"[BuildWiseFeeService] Fehler bei Rechnungsnummer-Generierung: {e}")
            # Fallback: Verwende Quote-ID basierte Nummer
            invoice_number = f"BW-{quote_id:06d}"
        
        print(f"[BuildWiseFeeService] Generiere Rechnung: {invoice_number}")
        
        # Berechne Fälligkeitsdatum (+30 Tage ab heute)
        invoice_date = date.today()
        due_date = invoice_date + timedelta(days=30)
        
        # Berechne Steuerbeträge (8.1% MwSt. Schweiz)
        tax_rate = Decimal("8.1")
        net_amount = Decimal(str(fee_amount))
        tax_amount = (net_amount * (tax_rate / Decimal("100.0"))).quantize(Decimal("0.01"))
        gross_amount = (net_amount + tax_amount).quantize(Decimal("0.01"))
        
        # Erstelle die Gebühr
        fee_data = BuildWiseFeeCreate(
            project_id=int(quote.project_id),
            quote_id=quote_id,
            cost_position_id=cost_position_id,
            service_provider_id=int(quote.service_provider_id),
            fee_amount=net_amount,
            fee_percentage=Decimal(str(fee_percentage)),
            quote_amount=Decimal(str(quote_amount)),
            currency=str(quote.currency),
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            due_date=due_date,
            status='open',
            invoice_pdf_generated=False,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            net_amount=net_amount,
            gross_amount=gross_amount,
            fee_details=f"BuildWise Vermittlungsgebühr ({fee_percentage}%) für akzeptiertes Angebot '{quote.title}'",
            notes=f"Automatisch generiert bei Angebotsannahme am {invoice_date.strftime('%d.%m.%Y')}. Fällig am {due_date.strftime('%d.%m.%Y')}."
        )
        
        # Erstelle das BuildWiseFee-Objekt
        fee = BuildWiseFee(**fee_data.dict())
        db.add(fee)
        
        try:
            await db.commit()
            await db.refresh(fee)
            
            print(f"[BuildWiseFeeService] Gebuehr erfolgreich erstellt:")
            print(f"   - ID: {fee.id}")
            print(f"   - Rechnungsnummer: {fee.invoice_number}")
            print(f"   - Nettobetrag: {fee.net_amount} {fee.currency}")
            print(f"   - Bruttobetrag: {fee.gross_amount} {fee.currency}")
            print(f"   - Provisionssatz: {fee.fee_percentage}%")
            print(f"   - Faelligkeitsdatum: {fee.due_date}")
            print(f"   - Status: {fee.status}")
            
            # Zusätzliche Validierung nach dem Speichern
            if not fee.id:
                raise ValueError("Gebühr wurde nicht korrekt gespeichert (keine ID)")
            
            return fee
            
        except IntegrityError as ie:
            await db.rollback()
            error_msg = f"Datenbank-Integritätsfehler beim Speichern der Gebühr: {str(ie)}"
            print(f"[BuildWiseFeeService] {error_msg}")
            # Prüfe ob es ein Duplikat-Fehler ist
            if "duplicate" in str(ie).lower() or "unique" in str(ie).lower():
                # Versuche die existierende Gebühr zu finden und zurückzugeben
                try:
                    existing_fee_query = select(BuildWiseFee).where(BuildWiseFee.quote_id == quote_id)
                    existing_fee_result = await db.execute(existing_fee_query)
                    existing_fee = existing_fee_result.scalar_one_or_none()
                    if existing_fee:
                        print(f"[BuildWiseFeeService] Duplikat erkannt, gebe existierende Gebuehr zurueck: {existing_fee.id}")
                        return existing_fee
                except Exception:
                    pass
            raise ValueError(error_msg)
            
        except Exception as e:
            await db.rollback()
            error_msg = f"Unerwarteter Fehler beim Speichern der Gebühr: {str(e)}"
            print(f"[BuildWiseFeeService] {error_msg}")
            import traceback
            traceback.print_exc()
            raise ValueError(error_msg)
    
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
            print(f"[DEBUG] BuildWiseFeeService.get_fees aufgerufen mit: skip={skip}, limit={limit}, project_id={project_id}, status={status}, month={month}, year={year}")
            
            # Robuste Prüfung: Prüfe ob Tabelle existiert und Daten hat
            try:
                # Zuerst: Prüfe alle Datensätze ohne Filter
                all_fees_query = select(BuildWiseFee)
                all_result = await db.execute(all_fees_query)
                all_fees = all_result.scalars().all()
                print(f"[DEBUG] Gesamtanzahl Datensätze in DB: {len(all_fees)}")
                
                # Wenn keine Daten vorhanden sind, gib leere Liste zurück
                if len(all_fees) == 0:
                    print("[WARNING] Debug: Keine Datensätze in buildwise_fees Tabelle gefunden")
                    print("[INFO] Tipp: Führen Sie ensure_buildwise_fees_data.py aus")
                    return []
                
                # Zeige alle Datensätze für Debug
                for i, fee in enumerate(all_fees):
                    print(f"  Datensatz {i+1}: ID={fee.id}, Project={fee.project_id}, Status={fee.status}, Amount={fee.fee_amount}")
                    
            except Exception as table_error:
                print(f"[WARNING] Debug: Fehler beim Zugriff auf buildwise_fees Tabelle: {table_error}")
                print("[INFO] Tipp: Prüfen Sie die Datenbank-Migrationen")
                return []
            
            # Hauptquery mit Filtern
            query = select(BuildWiseFee)
            
            # Filter anwenden
            if project_id:
                query = query.where(BuildWiseFee.project_id == project_id)
                print(f"[DEBUG] Filter für project_id={project_id} angewendet")
            
            if status:
                query = query.where(BuildWiseFee.status == status)
                print(f"[DEBUG] Filter für status={status} angewendet")
            
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
                print(f"[DEBUG] Datum-Filter angewendet: {start_date} bis {end_date} (inkl. NULL-Werte)")
            
            # Pagination
            query = query.offset(skip).limit(limit)
            
            print("[DEBUG] Führe gefilterte Query aus...")
            result = await db.execute(query)
            fees = result.scalars().all()
            
            print(f"[SUCCESS] Debug: {len(fees)} Gebühren nach Filterung gefunden")
            
            # Zeige gefilterte Datensätze für Debug
            for i, fee in enumerate(fees):
                print(f"  Gefilterter Datensatz {i+1}: ID={fee.id}, Project={fee.project_id}, Status={fee.status}, Amount={fee.fee_amount}")
            
            # Konvertiere zu Liste
            fees_list = list(fees)
            print(f"[SUCCESS] Debug: {len(fees_list)} Gebühren erfolgreich geladen")
            return fees_list
            
        except Exception as e:
            print(f"[ERROR] Debug: Fehler in get_fees: {str(e)}")
            import traceback
            traceback.print_exc()
            # Bei Fehlern gib leere Liste zurück statt Exception zu werfen
            print("[WARNING] Debug: Gebe leere Liste zurück bei Fehler")
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
    async def get_statistics(db: AsyncSession, service_provider_id: Optional[int] = None) -> BuildWiseFeeStatistics:
        """Holt Statistiken für BuildWise-Gebühren."""
        
        try:
            if service_provider_id:
                print(f"[DEBUG] Lade BuildWise-Gebühren Statistiken für Dienstleister {service_provider_id}...")
            else:
                print("[DEBUG] Lade BuildWise-Gebühren Statistiken (alle)...")
            
            # Base query mit optionalem Service Provider Filter
            base_query = select(BuildWiseFee)
            if service_provider_id:
                base_query = base_query.where(BuildWiseFee.service_provider_id == service_provider_id)
            
            # Gesamtanzahl
            total_fees_query = select(func.count(BuildWiseFee.id))
            if service_provider_id:
                total_fees_query = total_fees_query.where(BuildWiseFee.service_provider_id == service_provider_id)
            total_fees_result = await db.execute(total_fees_query)
            total_fees = total_fees_result.scalar() or 0
            print(f"   - Gesamtanzahl Gebühren: {total_fees}")
            
            # Gesamtbetrag
            total_amount_query = select(func.sum(BuildWiseFee.fee_amount))
            if service_provider_id:
                total_amount_query = total_amount_query.where(BuildWiseFee.service_provider_id == service_provider_id)
            total_amount_result = await db.execute(total_amount_query)
            total_amount = total_amount_result.scalar() or Decimal("0.0")
            print(f"   - Gesamtbetrag: {total_amount}")
            
            # Bezahlte Gebühren
            paid_query = select(func.sum(BuildWiseFee.fee_amount)).where(BuildWiseFee.status == 'paid')
            if service_provider_id:
                paid_query = paid_query.where(BuildWiseFee.service_provider_id == service_provider_id)
            paid_result = await db.execute(paid_query)
            total_paid = paid_result.scalar() or Decimal("0.0")
            print(f"   - Bezahlt: {total_paid}")
            
            # Aktuelles Datum für Fälligkeitsberechnung
            today = date.today()
            
            # Offene Gebühren - Status 'open'
            open_query = select(func.sum(BuildWiseFee.fee_amount)).where(BuildWiseFee.status == 'open')
            if service_provider_id:
                open_query = open_query.where(BuildWiseFee.service_provider_id == service_provider_id)
            open_result = await db.execute(open_query)
            total_open = open_result.scalar() or Decimal("0.0")
            print(f"   - Offen: {total_open}")
            
            # Überfällige Gebühren - basierend auf Fälligkeitsdatum, nicht Status
            overdue_query = select(func.sum(BuildWiseFee.fee_amount)).where(
                BuildWiseFee.due_date < today,
                BuildWiseFee.status != 'paid'  # Bezahlte Gebühren sind nicht überfällig
            )
            if service_provider_id:
                overdue_query = overdue_query.where(BuildWiseFee.service_provider_id == service_provider_id)
            overdue_result = await db.execute(overdue_query)
            total_overdue = overdue_result.scalar() or Decimal("0.0")
            print(f"   - Überfällig: {total_overdue}")
        
        except Exception as e:
            print(f"[ERROR] Debug: Fehler bei Basis-Statistiken: {e}")
            # Fallback-Werte
            total_fees = 0
            total_amount = Decimal("0.0")
            total_paid = Decimal("0.0")
            total_open = Decimal("0.0")
            total_overdue = Decimal("0.0")
        
        # Monatliche Aufschlüsselung - mit Fehlerbehandlung
        monthly_breakdown = []
        try:
            monthly_query = select(
                extract('month', BuildWiseFee.invoice_date).label('month'),
                extract('year', BuildWiseFee.invoice_date).label('year'),
                func.sum(BuildWiseFee.fee_amount).label('amount'),
                func.count(BuildWiseFee.id).label('count')
            ).where(
                BuildWiseFee.invoice_date.is_not(None)
            )
            
            if service_provider_id:
                monthly_query = monthly_query.where(BuildWiseFee.service_provider_id == service_provider_id)
            
            monthly_query = monthly_query.group_by(
                extract('month', BuildWiseFee.invoice_date),
                extract('year', BuildWiseFee.invoice_date)
            ).order_by(
                extract('year', BuildWiseFee.invoice_date).desc(),
                extract('month', BuildWiseFee.invoice_date).desc()
            ).limit(12)
            
            monthly_result = await db.execute(monthly_query)
            for row in monthly_result:
                if row.month is not None and row.year is not None:
                    monthly_breakdown.append({
                        'month': int(row.month),
                        'year': int(row.year),
                        'amount': float(row.amount or 0),
                        'count': int(row.count or 0)
                    })
            print(f"   - Monatliche Aufschlüsselung: {len(monthly_breakdown)} Einträge")
        
        except Exception as e:
            print(f"[ERROR] Debug: Fehler bei monatlicher Aufschlüsselung: {e}")
            monthly_breakdown = []
        
        # Status-Aufschlüsselung - mit Fehlerbehandlung
        status_breakdown = {}
        try:
            status_query = select(
                BuildWiseFee.status,
                func.count(BuildWiseFee.id).label('count'),
                func.sum(BuildWiseFee.fee_amount).label('amount')
            )
            
            if service_provider_id:
                status_query = status_query.where(BuildWiseFee.service_provider_id == service_provider_id)
            
            status_query = status_query.group_by(BuildWiseFee.status)
            
            status_result = await db.execute(status_query)
            for row in status_result:
                status_breakdown[row.status] = {
                    'count': int(row.count),
                    'amount': float(row.amount or 0)
                }
            print(f"   - Status-Aufschlüsselung: {len(status_breakdown)} Einträge")
        
        except Exception as e:
            print(f"[ERROR] Debug: Fehler bei Status-Aufschlüsselung: {e}")
            status_breakdown = {}
        
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
    async def generate_gewerk_invoice_and_save_document(
        db: AsyncSession, 
        fee_id: int, 
        current_user_id: int
    ) -> dict:
        """
        Generiert eine PDF-Rechnung für eine Gebühr (nur Gewerk-Daten) 
        und speichert sie automatisch als Dokument.
        
        Args:
            db: Datenbank-Session
            fee_id: ID der BuildWise-Gebühr
            current_user_id: ID des aktuellen Benutzers
            
        Returns:
            dict: Ergebnis mit Erfolg/Fehler und Dokument-ID
        """
        
        from app.models.document import Document, DocumentType
        import shutil
        
        query = select(BuildWiseFee).where(BuildWiseFee.id == fee_id)
        result = await db.execute(query)
        fee = result.scalar_one_or_none()
        
        if not fee:
            return {"success": False, "error": "Gebühr nicht gefunden"}
        
        try:
            # Hole alle notwendigen Daten
            # Angebot
            quote_query = select(Quote).where(Quote.id == fee.quote_id)
            quote_result = await db.execute(quote_query)
            quote = quote_result.scalar_one_or_none()
            
            # Kostenposition (Gewerk)
            cost_position_query = select(CostPosition).where(CostPosition.id == fee.cost_position_id)
            cost_position_result = await db.execute(cost_position_query)
            cost_position = cost_position_result.scalar_one_or_none()
            
            if not quote or not cost_position:
                return {"success": False, "error": "Angebot oder Kostenposition nicht gefunden"}
            
            # Erstelle PDF-Generator
            pdf_generator = BuildWisePDFGenerator()
            
            # Erstelle Ausgabepfad für PDF
            invoices_dir = "storage/invoices"
            os.makedirs(invoices_dir, exist_ok=True)
            pdf_output_path = f"{invoices_dir}/buildwise_gewerk_invoice_{fee_id}.pdf"
            
            # Konvertiere SQLAlchemy-Objekte zu Dictionaries
            fee_data = {
                'id': fee.id,
                'invoice_number': fee.invoice_number or f"BW-{fee.id:06d}",
                'invoice_date': fee.invoice_date or datetime.utcnow(),
                'due_date': fee.due_date,
                'status': fee.status,
                'fee_amount': float(fee.fee_amount),
                'fee_percentage': float(fee.fee_percentage),
                'tax_rate': float(fee.tax_rate),
                'notes': fee.notes
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
            
            # Generiere PDF (nur Gewerk-Daten)
            success = pdf_generator.generate_gewerk_invoice_pdf(
                fee_data=fee_data,
                quote_data=quote_data,
                cost_position_data=cost_position_data,
                output_path=pdf_output_path
            )
            
            if not success:
                return {"success": False, "error": "PDF-Generierung fehlgeschlagen"}
            
            # Erstelle Dokument-Verzeichnis
            documents_dir = f"storage/uploads/project_{fee.project_id}"
            os.makedirs(documents_dir, exist_ok=True)
            
            # Kopiere PDF in Dokument-Verzeichnis
            document_filename = f"buildwise_gewerk_invoice_{fee_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
            document_path = f"{documents_dir}/{document_filename}"
            shutil.copy2(pdf_output_path, document_path)
            
            # Hole Dateigröße
            file_size = os.path.getsize(document_path)
            
            # Erstelle Dokument-Eintrag in der Datenbank
            document = Document(
                project_id=fee.project_id,
                uploaded_by=current_user_id,
                title=f"BuildWise Rechnung - {cost_position.title}",
                description=f"BuildWise-Gebühren-Rechnung für Gewerk: {cost_position.title}. Gebühr: {fee.fee_percentage}% = {fee.fee_amount} EUR",
                document_type=DocumentType.INVOICE,
                file_name=document_filename,
                file_path=document_path,
                file_size=file_size,
                mime_type="application/pdf",
                category="BuildWise Gebühren",
                tags="buildwise,gebühren,rechnung,gewerk",
                is_public=False,
                is_encrypted=False
            )
            
            db.add(document)
            await db.commit()
            await db.refresh(document)
            
            # Aktualisiere BuildWise-Gebühr
            fee.invoice_pdf_generated = True
            fee.invoice_pdf_path = pdf_output_path
            await db.commit()
            
            return {
                "success": True,
                "document_id": document.id,
                "document_path": document_path,
                "pdf_path": pdf_output_path,
                "message": f"PDF-Rechnung erfolgreich generiert und als Dokument gespeichert (ID: {document.id})"
            }
                
        except Exception as e:
            print(f"Fehler beim Generieren der Gewerk-PDF und Speichern als Dokument: {e}")
            return {"success": False, "error": f"Fehler: {str(e)}"}
    
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
        """
        Prüft auf überfällige Gebühren und markiert sie entsprechend.
        
        Eine Gebühr gilt als überfällig, wenn:
        - Status ist 'open' (noch nicht bezahlt)
        - Fälligkeitsdatum liegt in der Vergangenheit
        
        Returns:
            dict: Informationen über die aktualisierten Gebühren
        """
        
        today = date.today()
        print(f"🔍 [BuildWiseFeeService] Prüfe auf überfällige Gebühren (Stand: {today})")
        
        overdue_query = select(BuildWiseFee).where(
            and_(
                BuildWiseFee.status == 'open',
                BuildWiseFee.due_date < today.isoformat()
            )
        )
        
        overdue_result = await db.execute(overdue_query)
        overdue_fees = overdue_result.scalars().all()
        
        if not overdue_fees:
            print(f"✅ [BuildWiseFeeService] Keine überfälligen Gebühren gefunden")
            return {
                "message": "Keine überfälligen Gebühren gefunden",
                "overdue_count": 0,
                "updated_fees": []
            }
        
        # Markiere als überfällig
        updated_fee_ids = []
        for fee in overdue_fees:
            fee.status = 'overdue'
            fee.updated_at = datetime.utcnow()
            updated_fee_ids.append(fee.id)
            
            days_overdue = (today - fee.due_date).days
            print(f"⚠️ [BuildWiseFeeService] Gebühr {fee.invoice_number} ist {days_overdue} Tage überfällig")
        
        await db.commit()
        
        print(f"✅ [BuildWiseFeeService] {len(overdue_fees)} Gebühren als überfällig markiert")
        
        return {
            "message": f"{len(overdue_fees)} Gebühren als überfällig markiert",
            "overdue_count": len(overdue_fees),
            "updated_fees": updated_fee_ids
        }
    
    @staticmethod
    async def get_fees_for_service_provider(
        db: AsyncSession,
        service_provider_id: int,
        status: Optional[str] = None
    ) -> List[BuildWiseFee]:
        """
        Holt alle BuildWise-Gebühren für einen bestimmten Dienstleister.
        
        Dies ist die zentrale Methode für die /buildwise-fees Ansicht des Dienstleisters.
        
        Args:
            db: Datenbank-Session
            service_provider_id: ID des Dienstleisters
            status: Optional - Filter nach Status ('open', 'paid', 'overdue', 'cancelled')
            
        Returns:
            List[BuildWiseFee]: Liste aller Gebühren für diesen Dienstleister
        """
        
        print(f"[DEBUG] [BuildWiseFeeService] Lade Gebühren für Dienstleister {service_provider_id}")
        
        try:
            # Einfache Query ohne komplexe Joins - robuster Ansatz
            query = select(BuildWiseFee).where(
                BuildWiseFee.service_provider_id == service_provider_id
            )
            
            if status:
                query = query.where(BuildWiseFee.status == status)
                print(f"   - Filter: Status = {status}")
            
            # Sortierung nach created_at falls due_date NULL ist
            query = query.order_by(
                BuildWiseFee.due_date.desc().nulls_last(),
                BuildWiseFee.created_at.desc()
            )
            
            result = await db.execute(query)
            fees = result.scalars().all()
            
            print(f"[SUCCESS] [BuildWiseFeeService] {len(fees)} Gebühren gefunden")
            
            return list(fees)
            
        except Exception as e:
            print(f"[ERROR] [BuildWiseFeeService] Fehler beim Laden der Gebühren für Dienstleister {service_provider_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Fallback: Leere Liste zurückgeben statt Exception zu werfen
            return [] 