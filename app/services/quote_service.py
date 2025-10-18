from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
from fastapi import HTTPException

from ..models import Quote, QuoteStatus, User, Project, Milestone, CostPosition, Appointment
from ..models.appointment_response import AppointmentResponse
from ..schemas.quote import QuoteCreate, QuoteUpdate, QuoteRead
from ..core.exceptions import QuoteNotFoundException, InvalidQuoteStatusException
from ..services.cost_position_service import get_cost_position_by_quote_id
from ..services.notification_service import NotificationService


async def _ensure_quote_notification_robust(db: AsyncSession, quote) -> bool:
    """
    ROBUSTE BENACHRICHTIGUNGSLÖSUNG für Quote Service
    
    Diese Funktion implementiert mehrfache Sicherheit für Benachrichtigungen:
    1. Prüft ob bereits eine Benachrichtigung existiert
    2. Erstellt eine neue Benachrichtigung falls keine existiert
    3. Loggt alle Schritte für Debugging
    4. Behandelt alle möglichen Fehler robust
    
    Returns:
        bool: True wenn Benachrichtigung erfolgreich gesendet wurde oder bereits existiert
    """
    try:
        from ..models.notification import Notification, NotificationType
        from sqlalchemy import select, and_
        
        print(f"\n{'='*60}")
        print(f"[QUOTE-SERVICE-BENACHRICHTIGUNG] Starte für Quote {quote.id}")
        print(f"{'='*60}")
        
        # 1. Prüfe ob bereits eine Benachrichtigung für dieses Angebot existiert
        existing_notification_result = await db.execute(
            select(Notification).where(
                and_(
                    Notification.related_quote_id == quote.id,
                    Notification.type == NotificationType.QUOTE_SUBMITTED
                )
            )
        )
        existing_notification = existing_notification_result.scalar_one_or_none()
        
        if existing_notification:
            print(f"[QUOTE-SERVICE-BENACHRICHTIGUNG] OK Benachrichtigung bereits vorhanden: ID {existing_notification.id}")
            return True
        
        # 2. Finde den Bauträger (Projektbesitzer)
        project_result = await db.execute(
            select(Project).where(Project.id == quote.project_id)
        )
        project = project_result.scalar_one_or_none()
        
        if not project or not project.owner_id:
            print(f"[QUOTE-SERVICE-BENACHRICHTIGUNG] FEHLER: Kein Bautraeger für Quote {quote.id} gefunden")
            return False
        
        print(f"[QUOTE-SERVICE-BENACHRICHTIGUNG] OK Bautraeger gefunden: ID {project.owner_id}")
        
        # 3. Erstelle Benachrichtigung mit mehrfacher Sicherheit
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"[QUOTE-SERVICE-BENACHRICHTIGUNG] Versuch {attempt + 1}/{max_retries}...")
                
                notification = await NotificationService.create_quote_submitted_notification(
                    db=db,
                    quote_id=quote.id,
                    recipient_id=project.owner_id
                )
                
                print(f"[QUOTE-SERVICE-BENACHRICHTIGUNG] ERFOLG: Benachrichtigung erstellt!")
                print(f"   Notification ID: {notification.id}")
                print(f"   Empfaenger: {notification.recipient_id}")
                print(f"{'='*60}\n")
                
                return True
                
            except Exception as e:
                print(f"[QUOTE-SERVICE-BENACHRICHTIGUNG] FEHLER: Versuch {attempt + 1} fehlgeschlagen: {e}")
                if attempt < max_retries - 1:
                    print(f"[QUOTE-SERVICE-BENACHRICHTIGUNG] Versuche erneut...")
                    continue
                else:
                    print(f"[QUOTE-SERVICE-BENACHRICHTIGUNG] FEHLER: Alle {max_retries} Versuche fehlgeschlagen")
                    raise e
        
    except Exception as e:
        print(f"[QUOTE-SERVICE-BENACHRICHTIGUNG] KRITISCHER FEHLER: {e}")
        print(f"   Fehlertyp: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        
        # Fehler bei Benachrichtigung sollte nicht die Quote-Erstellung blockieren
        return False


async def create_quote(db: AsyncSession, quote_in: QuoteCreate, service_provider_id: int) -> Quote:
    """Erstellt ein neues Angebot"""
    db_quote = Quote(
        project_id=quote_in.project_id,
        milestone_id=quote_in.milestone_id,
        service_provider_id=service_provider_id,
        title=quote_in.title,
        description=quote_in.description,
        status=quote_in.status,
        total_amount=quote_in.total_amount,
        currency=quote_in.currency,
        valid_until=quote_in.valid_until,
        labor_cost=quote_in.labor_cost,
        material_cost=quote_in.material_cost,
        overhead_cost=quote_in.overhead_cost,
        estimated_duration=quote_in.estimated_duration,
        start_date=quote_in.start_date,
        completion_date=quote_in.completion_date,
        payment_terms=quote_in.payment_terms,
        warranty_period=quote_in.warranty_period,
        # Kontakt-Informationen
        quote_number=quote_in.quote_number,
        company_name=quote_in.company_name,
        contact_person=quote_in.contact_person,
        phone=quote_in.phone,
        email=quote_in.email,
        website=quote_in.website,
        # Qualifikationen und Referenzen
        qualifications=quote_in.qualifications,
        references=quote_in.references,
        certifications=quote_in.certifications,
        # Technische Details
        technical_approach=quote_in.technical_approach,
        quality_standards=quote_in.quality_standards,
        safety_measures=quote_in.safety_measures,
        environmental_compliance=quote_in.environmental_compliance,
        # Risiko-Bewertung
        risk_assessment=quote_in.risk_assessment,
        contingency_plan=quote_in.contingency_plan,
        # Zusätzliche Informationen
        additional_notes=quote_in.additional_notes,
        pdf_upload_path=quote_in.pdf_upload_path,
        additional_documents=quote_in.additional_documents,
        rating=quote_in.rating,
        feedback=quote_in.feedback
    )
    db.add(db_quote)
    await db.commit()
    await db.refresh(db_quote)
    
    # ROBUSTE BENACHRICHTIGUNGSLÖSUNG - Mehrfache Sicherheit
    if db_quote.status == 'SUBMITTED' and db_quote.project_id:
        await _ensure_quote_notification_robust(db, db_quote)
    
    return db_quote


async def get_quote_by_id(db: AsyncSession, quote_id: int) -> Quote | None:
    """Holt ein Angebot anhand der ID inkl. zugehörigem Projekt (eager loading)"""
    result = await db.execute(
        select(Quote)
        .options(selectinload(Quote.project))
        .where(Quote.id == quote_id)
    )
    return result.scalar_one_or_none()


async def get_quotes_for_project(db: AsyncSession, project_id: int) -> List[Quote]:
    """Holt alle Angebote für ein Projekt"""
    result = await db.execute(
        select(Quote)
        .where(Quote.project_id == project_id)
        .order_by(Quote.created_at.desc())
    )
    return list(result.scalars().all())


async def get_quotes_for_milestone(db: AsyncSession, milestone_id: int) -> List[Quote]:
    """Holt alle Angebote für ein bestimmtes Gewerk"""
    try:
        print(f"[DEBUG] get_quotes_for_milestone: Suche Angebote für milestone_id={milestone_id}")
        result = await db.execute(
            select(Quote)
            .where(Quote.milestone_id == milestone_id)
            .order_by(Quote.total_amount.asc())  # Sortiert nach Preis (günstigste zuerst)
        )
        quotes = list(result.scalars().all())
        print(f"[DEBUG] get_quotes_for_milestone: Gefunden {len(quotes)} Angebote für milestone_id={milestone_id}")
        return quotes
    except Exception as e:
        print(f"[ERROR] get_quotes_for_milestone: Fehler beim Laden der Angebote für milestone_id={milestone_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


async def get_quotes_for_milestone_by_service_provider(db: AsyncSession, milestone_id: int, service_provider_id: int) -> List[Quote]:
    """Holt nur die Angebote eines bestimmten Dienstleisters für ein Gewerk"""
    result = await db.execute(
        select(Quote)
        .where(
            and_(
                Quote.milestone_id == milestone_id,
                Quote.service_provider_id == service_provider_id
            )
        )
        .order_by(Quote.created_at.desc())
    )
    return list(result.scalars().all())


async def get_quotes_for_service_provider(db: AsyncSession, service_provider_id: int) -> List[Quote]:
    """Holt alle Angebote eines Dienstleisters"""
    result = await db.execute(
        select(Quote)
        .where(Quote.service_provider_id == service_provider_id)
        .order_by(Quote.created_at.desc())
    )
    return list(result.scalars().all())


async def get_all_quotes(db: AsyncSession) -> List[Quote]:
    """Ruft alle Angebote ab (für Admin)"""
    result = await db.execute(select(Quote).options(selectinload(Quote.project)))
    return list(result.scalars().all())

async def get_quotes_by_project(db: AsyncSession, project_id: int) -> List[Quote]:
    """Ruft Angebote für ein bestimmtes Projekt ab"""
    result = await db.execute(
        select(Quote)
        .options(selectinload(Quote.project))
        .where(Quote.project_id == project_id)
    )
    return list(result.scalars().all())

async def get_quotes_by_service_provider(db: AsyncSession, service_provider_id: int) -> List[Quote]:
    """Ruft Angebote eines bestimmten Dienstleisters ab"""
    result = await db.execute(
        select(Quote)
        .options(selectinload(Quote.project))
        .where(Quote.service_provider_id == service_provider_id)
    )
    return list(result.scalars().all())


async def update_quote(db: AsyncSession, quote_id: int, quote_update: QuoteUpdate) -> Quote | None:
    """Aktualisiert ein Angebot"""
    quote = await get_quote_by_id(db, quote_id)
    if not quote:
        return None
    
    update_data = quote_update.dict(exclude_unset=True)
    if update_data:
        await db.execute(
            update(Quote)
            .where(Quote.id == quote_id)
            .values(**update_data, updated_at=datetime.utcnow())
        )
        await db.commit()
        await db.refresh(quote)
    
    return quote


async def delete_quote(db: AsyncSession, quote_id: int) -> bool:
    """Löscht ein Angebot"""
    quote = await get_quote_by_id(db, quote_id)
    if not quote:
        return False
    
    await db.delete(quote)
    await db.commit()
    return True


async def submit_quote(db: AsyncSession, quote_id: int) -> Quote | None:
    """Reicht ein Angebot ein"""
    quote = await get_quote_by_id(db, quote_id)
    if not quote:
        return None
    
    await db.execute(
        update(Quote)
        .where(Quote.id == quote_id)
        .values(
            status=QuoteStatus.SUBMITTED,
            submitted_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    )
    await db.commit()
    await db.refresh(quote)
    
    # ROBUSTE BENACHRICHTIGUNGSLÖSUNG - Auch bei nachträglicher Einreichung
    await _ensure_quote_notification_robust(db, quote)
    
    return quote


async def accept_quote(db: AsyncSession, quote_id: int) -> Quote | None:
    """Akzeptiert ein Angebot und erstellt Kostenposition sowie BuildWise Gebühr"""
    quote = await get_quote_by_id(db, quote_id)
    if not quote:
        return None
    
    # Setze alle anderen Angebote für das gleiche Gewerk auf "rejected"
    if quote.milestone_id is not None:
        await db.execute(
            update(Quote)
            .where(
                and_(
                    Quote.milestone_id == quote.milestone_id,
                    Quote.id != quote_id,
                    Quote.status == QuoteStatus.SUBMITTED
                )
            )
            .values(
                status=QuoteStatus.REJECTED,
                updated_at=datetime.utcnow()
            )
        )
    
    # Akzeptiere das Angebot und gib Kontaktdaten frei
    await db.execute(
        update(Quote)
        .where(Quote.id == quote_id)
        .values(
            status=QuoteStatus.ACCEPTED,
            accepted_at=datetime.utcnow(),
            contact_released=True,
            contact_released_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    )
    
    # [SUCCESS] WICHTIG: Erstelle Kostenposition für Finanzen-Übersicht auf Startseite
    # Diese Kostenposition erscheint beim Bauträger im Abschnitt "Finanzen"
    cost_position = await create_cost_position_from_quote(db, quote)
    
    # [SUCCESS] BUILDWISE GEBÜHR: Erstelle automatisch eine Vermittlungsgebühr (4.7%)
    # Diese wird in /buildwise-fees angezeigt und ist 30 Tage nach Angebotsannahme fällig
    buildwise_fee_created = False
    try:
        from ..services.buildwise_fee_service import BuildWiseFeeService
        from ..core.config import settings, get_fee_percentage
        
        print(f"\n{'='*80}")
        print(f"[QuoteService] ERSTELLE BUILDWISE GEBUEHR FÜR QUOTE {quote.id}")
        print(f"{'='*80}")
        print(f"   Quote ID: {quote.id}")
        print(f"   Quote Amount: {quote.total_amount} {quote.currency}")
        print(f"   Service Provider ID: {quote.service_provider_id}")
        print(f"   Project ID: {quote.project_id}")
        print(f"   Milestone ID: {quote.milestone_id}")
        print(f"   Environment Mode: {getattr(settings, 'environment_mode', 'production')}")
        print(f"   Fee Percentage: {get_fee_percentage()}%")
        
        # [SUCCESS] FIX: Da create_cost_position_from_quote deaktiviert wurde, verwende Quote-ID direkt
        # Die BuildWise Fee Service kann mit der Quote-ID arbeiten, ohne eine echte CostPosition zu benötigen
        cost_position_id = quote.id
        print(f"   Cost Position ID: {cost_position_id} (verwendet Quote-ID als Referenz)")
        
        # Erstelle BuildWise Gebühr mit Retry-Logik
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"\n[QuoteService] Versuch {attempt + 1}/{max_retries}...")
                
                buildwise_fee = await BuildWiseFeeService.create_fee_from_quote(
                    db=db,
                    quote_id=quote.id,
                    cost_position_id=cost_position_id,
                    fee_percentage=None  # Verwende automatisch den aktuellen Modus (4.7% in Production, 0% in Beta)
                )
                
                print(f"\n{'='*80}")
                print(f"[QuoteService] ERFOLG: BUILDWISE GEBUEHR ERSTELLT!")
                print(f"{'='*80}")
                print(f"   Fee ID: {buildwise_fee.id}")
                print(f"   Rechnungsnummer: {buildwise_fee.invoice_number}")
                print(f"   Nettobetrag: {buildwise_fee.fee_amount} {buildwise_fee.currency}")
                print(f"   Bruttobetrag (inkl. MwSt): {buildwise_fee.gross_amount} {buildwise_fee.currency}")
                print(f"   Provisionssatz: {buildwise_fee.fee_percentage}%")
                print(f"   Rechnungsdatum: {buildwise_fee.invoice_date}")
                print(f"   Faelligkeitsdatum: {buildwise_fee.due_date}")
                print(f"   Status: {buildwise_fee.status}")
                print(f"{'='*80}\n")
                
                buildwise_fee_created = True
                break  # Erfolgreich erstellt, verlasse Retry-Schleife
                
            except ValueError as ve:
                error_msg = str(ve)
                if "bereits" in error_msg.lower() or "existiert" in error_msg.lower():
                    # Gebühr existiert bereits - das ist OK
                    print(f"[QuoteService] INFO: BuildWise Gebuehr existiert bereits für Quote {quote.id}")
                    buildwise_fee_created = True
                    break
                elif "Pydantic" in error_msg or "validation" in error_msg.lower():
                    # Validierungsfehler - dies ist ein Programmierfehler
                    print(f"[QuoteService] FEHLER: Pydantic-Validierungsfehler bei Gebuehr-Erstellung:")
                    print(f"   {error_msg}")
                    print(f"   Dies deutet auf einen Rundungsfehler oder ungueltige Daten hin")
                    if attempt < max_retries - 1:
                        print(f"[QuoteService] Versuche erneut...")
                        continue
                    else:
                        print(f"[QuoteService] KRITISCH: Gebuehr konnte nach {max_retries} Versuchen nicht erstellt werden")
                        raise ve
                elif attempt < max_retries - 1:
                    print(f"[QuoteService] Versuch {attempt + 1} fehlgeschlagen: {ve}")
                    print(f"[QuoteService] Versuche erneut...")
                    continue
                else:
                    print(f"[QuoteService] FEHLER: Alle {max_retries} Versuche fehlgeschlagen")
                    raise ve
                    
            except Exception as e:
                print(f"[QuoteService] FEHLER bei Versuch {attempt + 1}: {type(e).__name__}: {e}")
                if attempt < max_retries - 1:
                    print(f"[QuoteService] Versuche erneut...")
                    import traceback
                    traceback.print_exc()
                    continue
                else:
                    print(f"[QuoteService] KRITISCH: Alle {max_retries} Versuche fehlgeschlagen")
                    raise e
        
    except ValueError as ve:
        # ValueError bedeutet, dass die Gebühr bereits existiert oder ein Validierungsfehler vorliegt
        print(f"\n[QuoteService] WARNUNG: BuildWise Gebuehr konnte nicht erstellt werden")
        print(f"   Fehlertyp: ValueError")
        print(f"   Fehlermeldung: {ve}")
        print(f"   Das Angebot wurde dennoch akzeptiert")
        import traceback
        traceback.print_exc()
        
    except Exception as e:
        print(f"\n[QuoteService] FEHLER: Unerwarteter Fehler beim Erstellen der BuildWise Gebuehr")
        print(f"   Fehlertyp: {type(e).__name__}")
        print(f"   Fehlermeldung: {e}")
        print(f"   Das Angebot wurde dennoch akzeptiert")
        import traceback
        traceback.print_exc()
        # Fehler beim Erstellen der Gebühr sollte nicht die Quote-Akzeptierung blockieren
        
    # Logging für Monitoring
    if buildwise_fee_created:
        print(f"\n[QuoteService] ERFOLG: BuildWise-Rechnungsstellung erfolgreich abgeschlossen fuer Quote {quote.id}")
    else:
        print(f"\n[QuoteService] ACHTUNG: BuildWise-Rechnungsstellung fuer Quote {quote.id} fehlgeschlagen")
        print(f"   Manueller Eingriff erforderlich!")
        print(f"   Verwenden Sie: python create_buildwise_fee_manually.py")
    
    # Credit-Zuordnung für Bauträger - ERWEITERT FÜR BESICHTIGUNGSSYSTEM
    try:
        from ..services.credit_service import CreditService
        from ..models.credit_event import CreditEventType
        from ..models.user import UserRole
        from ..models import Project
        from ..models.inspection import Inspection
        
        # Hole Projekt-Owner (Bauträger)
        project_result = await db.execute(
            select(Project).where(Project.id == quote.project_id)
        )
        project = project_result.scalar_one_or_none()
        
        # Hole die Owner-ID (project.owner ist eine User-Instanz, wir brauchen die ID)
        owner_id = project.owner.id if hasattr(project.owner, 'id') else project.owner_id
        
        if project and owner_id:
            # Prüfe ob dieses Angebot aus einem Besichtigungsprozess stammt
            inspection_result = await db.execute(
                select(Inspection)
                .join(Inspection.invitations)
                .where(
                    and_(
                        Inspection.milestone_id == quote.milestone_id,
                        Inspection.invitations.any(quote_id=quote.id)
                    )
                )
            )
            inspection = inspection_result.scalar_one_or_none()
            
            # Vergebe erhöhte Credits wenn Besichtigungsprozess durchlaufen wurde
            if inspection:
                # BONUS-CREDITS für vollständigen Besichtigungsprozess!
                await CreditService.reward_inspection_quote_acceptance(
                    db=db,
                    user_id=owner_id,
                    quote_id=quote.id,
                    inspection_id=inspection.id
                )
            else:
                # Standard-Credits für normale Angebotsakzeptanz
                await CreditService.add_credits_for_activity(
                    db=db,
                    user_id=owner_id,
                    event_type=CreditEventType.QUOTE_ACCEPTED,
                    description=f"Angebot akzeptiert: {quote.title}",
                    related_entity_type="quote",
                    related_entity_id=quote.id
                )
        
        # Zusätzliche Credit-Zuordnung (Legacy)
        if project and project.owner:
            try:
                owner = project.owner
                
                # Prüfe ob Owner ein Bauträger ist
                if owner.user_role == UserRole.BAUTRAEGER:
                    # Füge Credits für akzeptiertes Angebot hinzu
                    await CreditService.add_credits_for_activity(
                        db=db,
                        user_id=owner.id,
                        event_type=CreditEventType.QUOTE_ACCEPTED,
                        description=f"Angebot akzeptiert: {quote.title}",
                        related_entity_type="quote",
                        related_entity_id=quote.id
                    )
                    print(f"Credits fuer Bautraeger {owner.id} hinzugefuegt: Angebot akzeptiert")
                else:
                    print(f"Projekt-Owner {owner.id} ist kein Bautraeger, keine Credits hinzugefuegt")
            except Exception as credit_error:
                print(f"Fehler bei zusaetzlicher Credit-Zuordnung: {credit_error}")
                
    except Exception as e:
        print(f"Fehler bei Credit-Zuordnung: {e}")
        # Fehler bei Credit-Zuordnung sollte nicht die Quote-Akzeptierung blockieren
    
    # Erstelle Benachrichtigung für den Dienstleister
    try:
        from ..services.notification_service import NotificationService
        from ..models import Milestone
        from ..schemas.notification import NotificationCreate
        from ..models.notification import NotificationType, NotificationPriority
        
        # Hole Milestone-Informationen für die Benachrichtigung
        milestone_result = await db.execute(
            select(Milestone).where(Milestone.id == quote.milestone_id)
        )
        milestone = milestone_result.scalar_one_or_none()
        
        if milestone:
            notification_data = NotificationCreate(
                recipient_id=quote.service_provider_id or quote.user_id,
                type=NotificationType.QUOTE_ACCEPTED,
                title='Angebot angenommen',
                message=f'Ihr Angebot für "{milestone.title}" wurde vom Bauträger angenommen. Sie können nun mit der Ausführung beginnen.',
                priority=NotificationPriority.HIGH,
                related_quote_id=quote.id,
                related_project_id=quote.project_id,
                related_milestone_id=quote.milestone_id
            )
            
            notification = await NotificationService.create_notification(
                db=db,
                notification_data=notification_data
            )
            
            print(f"Benachrichtigung fuer Dienstleister {quote.service_provider_id or quote.user_id} erstellt: Angebot {quote.id} angenommen")
        else:
            print(f"Milestone {quote.milestone_id} nicht gefunden - Benachrichtigung uebersprungen")
            
    except Exception as e:
        print(f"Fehler beim Erstellen der Benachrichtigung: {e}")
        # Fehler bei Benachrichtigung sollte nicht die Quote-Akzeptierung blockieren
    
    await db.commit()
    await db.refresh(quote)
    return quote


async def create_cost_position_from_quote(db: AsyncSession, quote: Quote):
    """Erstellt eine Kostenposition aus einem akzeptierten Angebot"""
    try:
        print(f"Erstelle Kostenposition aus Quote {quote.id} fuer Projekt {quote.project_id}")
        
        from ..models.cost_position import CostPosition
        from ..schemas.cost_position import CostPositionCreate
        from sqlalchemy import select

        # Prüfe, ob bereits eine Kostenposition für dieses Angebot existiert
        existing_cost_position_result = await db.execute(
            select(CostPosition).where(CostPosition.quote_id == quote.id)
        )
        existing_cost_position = existing_cost_position_result.scalar_one_or_none()
        
        if existing_cost_position:
            print(f"Kostenposition für Quote {quote.id} existiert bereits (ID: {existing_cost_position.id})")
            return existing_cost_position

        # Hole Milestone für project_id
        milestone_id = quote.milestone_id
        if milestone_id is None:
            print("Quote hat keinen milestone_id - ueberspringe Kostenposition-Erstellung")
            return None

        from ..models import Milestone
        milestone_result = await db.execute(select(Milestone).where(Milestone.id == milestone_id))
        milestone = milestone_result.scalar_one_or_none()
        if not milestone:
            print("Milestone nicht gefunden - kann project_id nicht bestimmen")
            return None

        # Bestimme Kategorie basierend auf Milestone-Titel
        category = "custom"
        if milestone.title:
            title_lower = milestone.title.lower()
            if any(keyword in title_lower for keyword in ["maler", "painting", "anstrich"]):
                category = "painting"
            elif any(keyword in title_lower for keyword in ["elektro", "electrical", "strom"]):
                category = "electrical"
            elif any(keyword in title_lower for keyword in ["sanitär", "plumbing", "wasser"]):
                category = "plumbing"
            elif any(keyword in title_lower for keyword in ["heizung", "heating", "wärme"]):
                category = "heating"
            elif any(keyword in title_lower for keyword in ["dach", "roof", "dachdecker"]):
                category = "roofing"
            elif any(keyword in title_lower for keyword in ["boden", "floor", "fliesen"]):
                category = "flooring"

        # Erstelle Kostenposition-Daten
        cost_position_data = CostPositionCreate(
            project_id=quote.project_id,
            invoice_id=None,  # Keine Rechnung verknüpft (wird später hinzugefügt)
            title=quote.title or f"Angebot: {milestone.title}",
            description=quote.description or f"Kostenposition aus angenommenem Angebot für {milestone.title}",
            amount=float(quote.total_amount) if quote.total_amount else 0.0,
            position_order=1,
            category=category,
            cost_type="quote_accepted",
            status="active",
            contractor_name=quote.company_name,
            quote_id=quote.id,
            milestone_id=milestone_id
        )

        # Erstelle die Kostenposition
        cost_position = CostPosition(**cost_position_data.dict())
        db.add(cost_position)
        await db.commit()
        await db.refresh(cost_position)
        
        print(f"✅ Kostenposition erstellt: ID {cost_position.id}, Betrag {cost_position.amount} EUR")
        return cost_position
        
    except Exception as e:
        print(f"Fehler beim Erstellen der Kostenposition: {e}")
        # Rollback bei Fehlern
        await db.rollback()
        # Fehler weiterwerfen, damit er im Frontend sichtbar wird
        raise Exception(f"Fehler beim Erstellen der Kostenposition fuer Quote {quote.id}: {str(e)}")


async def get_quote_statistics(db: AsyncSession, project_id: int) -> dict:
    """Holt Statistiken für Angebote eines Projekts"""
    # Gesamtzahl der Angebote
    total_quotes = await db.execute(
        select(func.count(Quote.id))
        .where(Quote.project_id == project_id)
    )
    total_count = total_quotes.scalar()
    
    # Angebote nach Status
    status_counts = await db.execute(
        select(Quote.status, func.count(Quote.id))
        .where(Quote.project_id == project_id)
        .group_by(Quote.status)
    )
    status_stats = {status: count for status, count in status_counts.all()}
    
    # Durchschnittlicher Preis
    avg_price = await db.execute(
        select(func.avg(Quote.total_amount))
        .where(
            and_(
                Quote.project_id == project_id,
                Quote.status == QuoteStatus.SUBMITTED
            )
        )
    )
    average_price = avg_price.scalar() or 0
    
    # Höchster und niedrigster Preis
    price_range = await db.execute(
        select(
            func.min(Quote.total_amount),
            func.max(Quote.total_amount)
        )
        .where(
            and_(
                Quote.project_id == project_id,
                Quote.status == QuoteStatus.SUBMITTED
            )
        )
    )
    min_price, max_price = price_range.first() or (0, 0)
    
    return {
        "total_quotes": total_count,
        "status_distribution": status_stats,
        "average_price": float(average_price),
        "price_range": {
            "min": float(min_price) if min_price else 0,
            "max": float(max_price) if max_price else 0
        }
    }


async def analyze_quote(db: AsyncSession, quote_id: int) -> dict:
    """Analysiert ein Angebot mit KI"""
    quote = await get_quote_by_id(db, quote_id)
    if not quote:
        return {}
    
    # Hole alle anderen Angebote für das gleiche Gewerk zum Vergleich
    comparison_quotes = []
    if quote.milestone_id is not None:
        result = await db.execute(
            select(Quote.total_amount)
            .where(
                and_(
                    Quote.milestone_id == quote.milestone_id,
                    Quote.id != quote_id,
                    Quote.status == QuoteStatus.SUBMITTED
                )
            )
        )
        comparison_quotes = result.scalars().all()
    
    # Berechne Risiko-Score und Preisabweichung
    risk_score = 15  # Standard-Risiko
    price_deviation = 0
    
    if comparison_quotes:
        avg_price = sum(comparison_quotes) / len(comparison_quotes)
        price_deviation = ((quote.total_amount - avg_price) / avg_price) * 100
        
        # Risiko-Score basierend auf Preisabweichung
        if abs(price_deviation) > 30:
            risk_score = 35
        elif abs(price_deviation) > 15:
            risk_score = 25
        else:
            risk_score = 15
    
    # KI-Empfehlung
    if price_deviation < -20:
        ai_recommendation = "Günstigster Preis, aber höheres Risiko"
    elif price_deviation < -5:
        ai_recommendation = "Empfohlen - Gutes Preis-Leistungs-Verhältnis"
    elif price_deviation < 10:
        ai_recommendation = "Fairer Preis im Marktdurchschnitt"
    else:
        ai_recommendation = "Höherer Preis, aber möglicherweise bessere Qualität"
    
    # Aktualisiere das Angebot mit der Analyse
    await db.execute(
        update(Quote)
        .where(Quote.id == quote_id)
        .values(
            risk_score=risk_score,
            price_deviation=price_deviation,
            ai_recommendation=ai_recommendation,
            updated_at=datetime.utcnow()
        )
    )
    
    await db.commit()
    
    return {
        "quote_id": quote_id,
        "risk_score": risk_score,
        "price_deviation": price_deviation,
        "ai_recommendation": ai_recommendation,
        "comparison_data": {
            "total_comparison_quotes": len(comparison_quotes),
            "average_price": sum(comparison_quotes) / len(comparison_quotes) if comparison_quotes else 0
        }
    }


async def create_mock_quotes_for_milestone(db: AsyncSession, milestone_id: int, project_id: int) -> List[Quote]:
    """Erstellt Mock-Angebote für ein Gewerk (für Demonstrationszwecke)"""
    
    # Prüfe zuerst, ob bereits Angebote für dieses Gewerk existieren
    existing_quotes = await get_quotes_for_milestone(db, milestone_id)
    if existing_quotes:
        print(f"[SUCCESS] Bereits {len(existing_quotes)} Angebote für Gewerk {milestone_id} vorhanden")
        return existing_quotes
    
    # Hole Gewerk-Informationen für passende Angebote
    from ..models import Milestone
    milestone_result = await db.execute(select(Milestone).where(Milestone.id == milestone_id))
    milestone = milestone_result.scalar_one_or_none()
    
    # Erstelle passende Mock-Angebote basierend auf dem Gewerk-Titel
    milestone_title = milestone.title.lower() if milestone and milestone.title else "elektro"
    
    if "elektro" in milestone_title:
        mock_quotes_data = [
            {
                "title": "Elektroinstallation - Premium",
                "description": "Komplette Elektroinstallation inkl. Smart Home, KNX-System und Photovoltaik-Anschluss. Verwendete Materialien: Hager Schaltschränke, Busch-Jaeger Schalter, Jung Kabel, Siemens Sicherungen, KNX-Bus-System, Smart Home Steuerung, Photovoltaik-Anschlussbox.",
                "total_amount": 45000,
                "labor_cost": 25000,
                "material_cost": 15000,
                "overhead_cost": 5000,
                "estimated_duration": 45,
                "start_date": date(2024, 3, 1),
                "completion_date": date(2024, 4, 15),
                "payment_terms": "30 Tage nach Rechnung",
                "warranty_period": 24,
                "company_name": "Elektro Meier GmbH",
                "contact_person": "Hans Meier",
                "phone": "+49 123 456789",
                "email": "hans.meier@elektro-meier.de",
                "website": "www.elektro-meier.de",
                "ai_recommendation": "Empfohlen - Gutes Preis-Leistungs-Verhältnis"
            },
            {
                "title": "Elektroinstallation - Standard",
                "description": "Standard Elektroinstallation mit modernen Sicherheitssystemen. Verwendete Materialien: Siemens Schaltschränke, Gira Schalter, Lapp Kabel, Hager Sicherungen, FI-Schutzschalter, LED-Beleuchtung, Steckdosen mit USB-Anschluss.",
                "total_amount": 52000,
                "labor_cost": 30000,
                "material_cost": 17000,
                "overhead_cost": 5000,
                "estimated_duration": 50,
                "start_date": date(2024, 3, 5),
                "completion_date": date(2024, 4, 25),
                "payment_terms": "50% bei Auftrag, Rest bei Fertigstellung",
                "warranty_period": 36,
                "company_name": "Elektro Schmidt & Partner",
                "contact_person": "Klaus Schmidt",
                "phone": "+49 987 654321",
                "email": "klaus.schmidt@elektro-schmidt.de",
                "website": "www.elektro-schmidt.de",
                "ai_recommendation": "Höherer Preis, aber längere Garantie"
            },
            {
                "title": "Elektroinstallation - Budget",
                "description": "Günstige Elektroinstallation mit Grundausstattung. Verwendete Materialien: Standard Schaltschränke, Berker Schalter, Standard Kabel, Sicherungen, Grundlegende Beleuchtung, Standard Steckdosen.",
                "total_amount": 38000,
                "labor_cost": 20000,
                "material_cost": 13000,
                "overhead_cost": 5000,
                "estimated_duration": 40,
                "start_date": date(2024, 3, 1),
                "completion_date": date(2024, 4, 10),
                "payment_terms": "100% bei Fertigstellung",
                "warranty_period": 24,
                "company_name": "Schnell & Günstig Elektro",
                "contact_person": "Peter Schnell",
                "phone": "+49 555 123456",
                "email": "peter.schnell@schnell-elektro.de",
                "website": "www.schnell-elektro.de",
                "ai_recommendation": "Günstigster Preis, aber höheres Risiko"
            }
        ]
    elif "sanitär" in milestone_title or "wasser" in milestone_title:
        mock_quotes_data = [
            {
                "title": "Sanitäranlagen - Premium",
                "description": "Komplette Sanitäranlagen mit Design-Armaturen und Wellness-Bereich. Verwendete Materialien: Grohe Armaturen, Villeroy & Boch Sanitäranlagen, Hansgrohe Duschsysteme, Geberit Spülkästen, Rehau Rohre, Wellness-Dusche mit Massagefunktion.",
                "total_amount": 35000,
                "labor_cost": 20000,
                "material_cost": 12000,
                "overhead_cost": 3000,
                "estimated_duration": 35,
                "start_date": date(2024, 3, 1),
                "completion_date": date(2024, 4, 5),
                "payment_terms": "30 Tage nach Rechnung",
                "warranty_period": 24,
                "company_name": "Sanitär Müller GmbH",
                "contact_person": "Thomas Müller",
                "phone": "+49 111 222333",
                "email": "thomas.mueller@sanitaer-mueller.de",
                "website": "www.sanitaer-mueller.de",
                "ai_recommendation": "Empfohlen - Gutes Preis-Leistungs-Verhältnis"
            },
            {
                "title": "Sanitäranlagen - Standard",
                "description": "Standard Sanitäranlagen mit Qualitätsarmaturen. Verwendete Materialien: Hansgrohe Armaturen, Duravit Sanitäranlagen, Kludi Duschsysteme, Geberit Spülkästen, Rehau Rohre, Standard-Dusche.",
                "total_amount": 42000,
                "labor_cost": 25000,
                "material_cost": 14000,
                "overhead_cost": 3000,
                "estimated_duration": 40,
                "start_date": date(2024, 3, 5),
                "completion_date": date(2024, 4, 15),
                "payment_terms": "50% bei Auftrag, Rest bei Fertigstellung",
                "warranty_period": 36,
                "company_name": "Sanitär Weber & Co.",
                "contact_person": "Michael Weber",
                "phone": "+49 444 555666",
                "email": "michael.weber@sanitaer-weber.de",
                "website": "www.sanitaer-weber.de",
                "ai_recommendation": "Höherer Preis, aber längere Garantie"
            },
            {
                "title": "Sanitäranlagen - Budget",
                "description": "Günstige Sanitäranlagen mit Grundausstattung. Verwendete Materialien: Standard Armaturen, Keramag Sanitäranlagen, Kludi Duschsysteme, Geberit Spülkästen, Standard Rohre, Einfache Dusche.",
                "total_amount": 28000,
                "labor_cost": 15000,
                "material_cost": 10000,
                "overhead_cost": 3000,
                "estimated_duration": 30,
                "start_date": date(2024, 3, 1),
                "completion_date": date(2024, 3, 31),
                "payment_terms": "100% bei Fertigstellung",
                "warranty_period": 24,
                "company_name": "Schnell Sanitär",
                "contact_person": "Andreas Schnell",
                "phone": "+49 777 888999",
                "email": "andreas.schnell@schnell-sanitaer.de",
                "website": "www.schnell-sanitaer.de",
                "ai_recommendation": "Günstigster Preis, aber höheres Risiko"
            }
        ]
    else:
        # Generische Angebote für andere Gewerke
        milestone_name = milestone.title if milestone and milestone.title else "Gewerk"
        mock_quotes_data = [
            {
                "title": f"{milestone_name} - Premium",
                "description": f"Premium {milestone_name} mit hochwertigen Materialien. Verwendete Materialien: Premium-Materialien, Markenprodukte, hochwertige Werkzeuge, Qualitätsgarantie, professionelle Ausführung.",
                "total_amount": 40000,
                "labor_cost": 22000,
                "material_cost": 14000,
                "overhead_cost": 4000,
                "estimated_duration": 40,
                "start_date": date(2024, 3, 1),
                "completion_date": date(2024, 4, 10),
                "payment_terms": "30 Tage nach Rechnung",
                "warranty_period": 24,
                "company_name": f"{milestone_name} Premium GmbH",
                "contact_person": "Max Mustermann",
                "phone": "+49 123 456789",
                "email": "max.mustermann@premium.de",
                "website": "www.premium.de",
                "ai_recommendation": "Empfohlen - Gutes Preis-Leistungs-Verhältnis"
            },
            {
                "title": f"{milestone_name} - Standard",
                "description": f"Standard {milestone_name} mit Qualitätsmaterialien. Verwendete Materialien: Standard-Materialien, bewährte Produkte, professionelle Werkzeuge, Qualitätsgarantie, zuverlässige Ausführung.",
                "total_amount": 48000,
                "labor_cost": 28000,
                "material_cost": 16000,
                "overhead_cost": 4000,
                "estimated_duration": 45,
                "start_date": date(2024, 3, 5),
                "completion_date": date(2024, 4, 20),
                "payment_terms": "50% bei Auftrag, Rest bei Fertigstellung",
                "warranty_period": 36,
                "company_name": f"{milestone_name} Standard GmbH",
                "contact_person": "Anna Schmidt",
                "phone": "+49 987 654321",
                "email": "anna.schmidt@standard.de",
                "website": "www.standard.de",
                "ai_recommendation": "Höherer Preis, aber längere Garantie"
            },
            {
                "title": f"{milestone_name} - Budget",
                "description": f"Günstige {milestone_name} mit Grundausstattung. Verwendete Materialien: Grundausstattung, Standard-Materialien, bewährte Werkzeuge, Grundgarantie, solide Ausführung.",
                "total_amount": 32000,
                "labor_cost": 18000,
                "material_cost": 11000,
                "overhead_cost": 3000,
                "estimated_duration": 35,
                "start_date": date(2024, 3, 1),
                "completion_date": date(2024, 4, 5),
                "payment_terms": "100% bei Fertigstellung",
                "warranty_period": 24,
                "company_name": f"Schnell {milestone_name}",
                "contact_person": "Peter Schnell",
                "phone": "+49 555 123456",
                "email": "peter.schnell@schnell.de",
                "website": "www.schnell.de",
                "ai_recommendation": "Günstigster Preis, aber höheres Risiko"
            }
        ]
    
    created_quotes = []
    for i, quote_data in enumerate(mock_quotes_data):
        quote = Quote(
            project_id=project_id,
            milestone_id=milestone_id,
            service_provider_id=i + 1,  # Mock service provider IDs
            status=QuoteStatus.SUBMITTED,
            submitted_at=datetime.utcnow(),
            **quote_data
        )
        db.add(quote)
        created_quotes.append(quote)
    
    await db.commit()
    
    # Aktualisiere alle Angebote mit der Analyse
    for quote in created_quotes:
        await analyze_quote(db, quote.id)
    
    print(f"[SUCCESS] {len(created_quotes)} neue Mock-Angebote für Gewerk '{milestone.title if milestone and milestone.title else milestone_id}' erstellt")
    return created_quotes


async def revise_quote_after_inspection(
    db: AsyncSession,
    quote_id: int,
    quote_update: QuoteUpdate,
    service_provider_id: int
) -> Quote:
    """
    Überarbeitet ein bestehendes Angebot nach einer Besichtigung.
    
    Validierungen:
    - Quote muss existieren
    - Service Provider muss der Ersteller sein
    - Quote muss SUBMITTED sein
    - Mindestens eine Besichtigung muss zugesagt worden sein (accepted)
    
    Aktionen:
    - Aktualisiert das Angebot
    - Setzt revised_after_inspection = True
    - Erhöht revision_count
    - Setzt last_revised_at
    - Erstellt Benachrichtigung für Bauträger
    """
    # Hole das Angebot
    quote = await get_quote_by_id(db, quote_id)
    if not quote:
        raise QuoteNotFoundException(f"Quote {quote_id} nicht gefunden")
    
    # Validiere Service Provider
    if quote.service_provider_id != service_provider_id:
        raise HTTPException(
            status_code=403,
            detail="Nur der Ersteller kann das Angebot überarbeiten"
        )
    
    # Validiere Status
    if quote.status != QuoteStatus.SUBMITTED:
        raise InvalidQuoteStatusException(
            f"Angebot kann nur im Status SUBMITTED überarbeitet werden (aktuell: {quote.status})"
        )
    
    # Validiere ob eine Besichtigung zugesagt wurde
    if quote.milestone_id:
        # Prüfe ob es Appointments für dieses Milestone gibt
        appointments_result = await db.execute(
            select(Appointment)
            .where(Appointment.milestone_id == quote.milestone_id)
            .where(Appointment.appointment_type == 'INSPECTION')
        )
        appointments = list(appointments_result.scalars().all())
        
        has_accepted_inspection = False
        
        # Prüfe in der appointment_responses Tabelle
        for apt in appointments:
            response_result = await db.execute(
                select(AppointmentResponse)
                .where(AppointmentResponse.appointment_id == apt.id)
                .where(AppointmentResponse.service_provider_id == service_provider_id)
                .where(AppointmentResponse.status == 'accepted')
            )
            response = response_result.scalar_one_or_none()
            
            if response:
                has_accepted_inspection = True
                print(f"[SUCCESS] Gefundene akzeptierte Besichtigung: Appointment {apt.id}, Response {response.id}")
                break
            
            # Fallback: Prüfe auch in der alten responses JSON-Spalte
            if apt.responses:
                try:
                    responses = json.loads(apt.responses) if isinstance(apt.responses, str) else apt.responses
                    if isinstance(responses, list):
                        for resp in responses:
                            if (resp.get('service_provider_id') == service_provider_id and 
                                resp.get('status') == 'accepted'):
                                has_accepted_inspection = True
                                print(f"[SUCCESS] Gefundene akzeptierte Besichtigung (JSON): Appointment {apt.id}")
                                break
                except:
                    pass
            
            if has_accepted_inspection:
                break
        
        if not has_accepted_inspection:
            print(f"[ERROR] Keine akzeptierte Besichtigung gefunden für Service Provider {service_provider_id}, Milestone {quote.milestone_id}")
            print(f"   Gefundene Appointments: {len(appointments)}")
            raise InvalidQuoteStatusException(
                "Angebot kann nur überarbeitet werden, wenn eine Besichtigung zugesagt wurde"
            )
    
    # Aktualisiere das Angebot
    update_data = quote_update.model_dump(exclude_unset=True)
    
    print(f"[INFO] Update-Daten erhalten: {len(update_data)} Felder")
    print(f"   Felder: {list(update_data.keys())}")
    
    # Debug: Zeige wichtige Felder
    if 'total_amount' in update_data:
        print(f"   [SUCCESS] total_amount: {update_data['total_amount']}")
    if 'description' in update_data:
        print(f"   [SUCCESS] description: {update_data['description'][:100]}...")
    if 'title' in update_data:
        print(f"   [SUCCESS] title: {update_data['title']}")
    
    # Setze Revisions-Felder
    update_data['revised_after_inspection'] = True
    update_data['revision_count'] = (quote.revision_count or 0) + 1
    update_data['last_revised_at'] = datetime.utcnow()
    update_data['is_revised_quote'] = True  # Kennzeichnet als überarbeitetes Angebot
    
    print(f"[UPDATE] Aktualisiere Quote {quote.id} mit {len(update_data)} Feldern")
    
    for key, value in update_data.items():
        old_value = getattr(quote, key, None)
        setattr(quote, key, value)
        if old_value != value and key in ['total_amount', 'title', 'description']:
            print(f"   [INFO] {key}: {old_value} -> {value}")
    
    await db.commit()
    await db.refresh(quote)
    
    print(f"[INFO] Quote {quote.id} in Datenbank gespeichert")
    print(f"   Neuer total_amount: {quote.total_amount}")
    print(f"   Revision Count: {quote.revision_count}")
    
    # Erstelle Benachrichtigung für Bauträger
    if quote.project_id:
        try:
            project_result = await db.execute(
                select(Project).where(Project.id == quote.project_id)
            )
            project = project_result.scalar_one_or_none()
            
            if project and project.owner_id:
                await NotificationService.create_quote_revised_notification(
                    db=db,
                    quote_id=quote.id,
                    recipient_id=project.owner_id,
                    milestone_id=quote.milestone_id
                )
                print(f"[SUCCESS] Benachrichtigung für überarbeitetes Quote {quote.id} an Bauträger {project.owner_id} erstellt")
        except Exception as e:
            print(f"[WARNING] Fehler beim Erstellen der Benachrichtigung: {e}")
    
    print(f"[SUCCESS] Angebot {quote_id} erfolgreich überarbeitet (Revision #{quote.revision_count})")
    return quote


async def can_revise_quote_after_inspection(
    db: AsyncSession,
    quote_id: int,
    service_provider_id: int
) -> bool:
    """
    Prüft ob ein Angebot nach Besichtigung überarbeitet werden kann.
    
    Returns:
        True wenn alle Bedingungen erfüllt sind, sonst False
    """
    try:
        quote = await get_quote_by_id(db, quote_id)
        if not quote:
            return False
        
        # Prüfe Service Provider
        if quote.service_provider_id != service_provider_id:
            return False
        
        # Prüfe Status
        if quote.status != QuoteStatus.SUBMITTED:
            return False
        
        # Prüfe ob Besichtigung zugesagt wurde
        if not quote.milestone_id:
            return False
        
        result = await db.execute(
            select(Appointment)
            .where(Appointment.milestone_id == quote.milestone_id)
            .where(Appointment.appointment_type == 'INSPECTION')
        )
        appointments = list(result.scalars().all())
        
        # Prüfe in der appointment_responses Tabelle
        for apt in appointments:
            response_result = await db.execute(
                select(AppointmentResponse)
                .where(AppointmentResponse.appointment_id == apt.id)
                .where(AppointmentResponse.service_provider_id == service_provider_id)
                .where(AppointmentResponse.status == 'accepted')
            )
            response = response_result.scalar_one_or_none()
            
            if response:
                return True
            
            # Fallback: Prüfe auch in der alten responses JSON-Spalte
            if apt.responses:
                try:
                    responses = json.loads(apt.responses) if isinstance(apt.responses, str) else apt.responses
                    if isinstance(responses, list):
                        for resp in responses:
                            if (resp.get('service_provider_id') == service_provider_id and 
                                resp.get('status') == 'accepted'):
                                return True
                except:
                    pass
        
        return False
        
    except Exception as e:
        print(f"[ERROR] Fehler beim Prüfen der Überarbeitungs-Berechtigung: {e}")
        return False 