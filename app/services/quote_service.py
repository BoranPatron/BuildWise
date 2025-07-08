from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_
from typing import List, Optional
from datetime import datetime, date
from sqlalchemy.orm import selectinload

from ..models import Quote, QuoteStatus
from ..schemas.quote import QuoteCreate, QuoteUpdate, QuoteForMilestone


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
        company_name=quote_in.company_name,
        contact_person=quote_in.contact_person,
        phone=quote_in.phone,
        email=quote_in.email,
        website=quote_in.website,
        pdf_upload_path=quote_in.pdf_upload_path,
        additional_documents=quote_in.additional_documents,
        rating=quote_in.rating,
        feedback=quote_in.feedback
    )
    db.add(db_quote)
    await db.commit()
    await db.refresh(db_quote)
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
    result = await db.execute(
        select(Quote)
        .where(Quote.milestone_id == milestone_id)
        .order_by(Quote.total_amount.asc())  # Sortiert nach Preis (günstigste zuerst)
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
    return quote


async def accept_quote(db: AsyncSession, quote_id: int) -> Quote | None:
    """Akzeptiert ein Angebot und erstellt Kostenposition"""
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
    
    # Erstelle Kostenposition für das akzeptierte Angebot
    await create_cost_position_from_quote(db, quote)
    
    await db.commit()
    await db.refresh(quote)
    return quote


async def create_cost_position_from_quote(db: AsyncSession, quote: Quote) -> bool:
    """Erstellt eine Kostenposition basierend auf einem akzeptierten Angebot"""
    try:
        from ..models import CostPosition, CostCategory, CostType, CostStatus
        
        # Bestimme die Kostenkategorie basierend auf dem Gewerk
        category_mapping = {
            'elektro': 'electrical',
            'sanitär': 'plumbing', 
            'heizung': 'heating',
            'dach': 'roofing',
            'mauerwerk': 'masonry',
            'trockenbau': 'drywall',
            'maler': 'painting',
            'boden': 'flooring',
            'garten': 'landscaping',
            'küche': 'kitchen',
            'bad': 'bathroom'
        }
        
        # Hole Gewerk-Informationen
        milestone_title = ""
        if quote.milestone_id:
            from ..models import Milestone
            milestone_result = await db.execute(
                select(Milestone).where(Milestone.id == quote.milestone_id)
            )
            milestone = milestone_result.scalar_one_or_none()
            if milestone and milestone.title:
                milestone_title = milestone.title.lower()
        
        # Bestimme Kategorie
        category = CostCategory.OTHER
        for keyword, cat in category_mapping.items():
            if keyword in milestone_title:
                if cat == 'electrical':
                    category = CostCategory.ELECTRICAL
                elif cat == 'plumbing':
                    category = CostCategory.PLUMBING
                elif cat == 'heating':
                    category = CostCategory.HEATING
                elif cat == 'roofing':
                    category = CostCategory.ROOFING
                elif cat == 'masonry':
                    category = CostCategory.MASONRY
                elif cat == 'drywall':
                    category = CostCategory.DRYWALL
                elif cat == 'painting':
                    category = CostCategory.PAINTING
                elif cat == 'flooring':
                    category = CostCategory.FLOORING
                elif cat == 'landscaping':
                    category = CostCategory.LANDSCAPING
                elif cat == 'kitchen':
                    category = CostCategory.KITCHEN
                elif cat == 'bathroom':
                    category = CostCategory.BATHROOM
                break
        
        # Erstelle Kostenposition
        cost_position = CostPosition(
            project_id=quote.project_id,
            title=f"Kostenposition: {quote.title}",
            description=quote.description or f"Kostenposition für {quote.title}",
            amount=quote.total_amount,
            currency=quote.currency,
            category=category,
            cost_type=CostType.QUOTE_ACCEPTED,  # Spezieller Typ für akzeptierte Angebote
            status=CostStatus.ACTIVE,
            payment_terms=quote.payment_terms,
            warranty_period=quote.warranty_period,
            estimated_duration=quote.estimated_duration,
            start_date=quote.start_date,
            completion_date=quote.completion_date,
            contractor_name=quote.company_name,
            contractor_contact=quote.contact_person,
            contractor_phone=quote.phone,
            contractor_email=quote.email,
            contractor_website=quote.website,
            quote_id=quote.id,  # Verknüpfung zum ursprünglichen Angebot
            milestone_id=quote.milestone_id,
            service_provider_id=quote.service_provider_id,
            # Aufschlüsselung der Kosten
            labor_cost=quote.labor_cost,
            material_cost=quote.material_cost,
            overhead_cost=quote.overhead_cost,
            # Zusätzliche Informationen
            risk_score=quote.risk_score,
            price_deviation=quote.price_deviation,
            ai_recommendation=quote.ai_recommendation
        )
        
        db.add(cost_position)
        await db.commit()
        
        print(f"✅ Kostenposition für Angebot '{quote.title}' erstellt (ID: {cost_position.id})")
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Kostenposition: {e}")
        return False


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
        print(f"✅ Bereits {len(existing_quotes)} Angebote für Gewerk {milestone_id} vorhanden")
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
    
    print(f"✅ {len(created_quotes)} neue Mock-Angebote für Gewerk '{milestone.title if milestone and milestone.title else milestone_id}' erstellt")
    return created_quotes 