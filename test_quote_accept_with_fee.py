#!/usr/bin/env python3
"""
Test Script: Simuliert das Akzeptieren eines neuen Quotes und überprüft ob die BuildWise-Gebühr automatisch erstellt wird
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add app directory to path
sys.path.insert(0, '.')

async def test_accept_new_quote():
    """Teste Quote Accept mit automatischer BuildWise-Gebühr Erstellung"""
    
    # Create async engine
    DATABASE_URL = "sqlite+aiosqlite:///./buildwise.db"
    engine = create_async_engine(DATABASE_URL, echo=False)  # echo=False für sauberere Ausgabe
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            from app.models.quote import Quote, QuoteStatus
            from app.services.quote_service import accept_quote
            from app.models.buildwise_fee import BuildWiseFee
            from sqlalchemy import select
            
            print("\n" + "="*80)
            print("TEST: QUOTE ACCEPT MIT AUTOMATISCHER BUILDWISE-GEBUEHR")
            print("="*80)
            
            # Suche nach einem SUBMITTED Quote (nicht Quote 1, da das bereits akzeptiert ist)
            print("\n1. Suche nach einem SUBMITTED Quote zum Testen...")
            quote_result = await db.execute(
                select(Quote).where(Quote.status == QuoteStatus.SUBMITTED).limit(1)
            )
            test_quote = quote_result.scalar_one_or_none()
            
            if not test_quote:
                print("   HINWEIS: Kein SUBMITTED Quote gefunden.")
                print("   Erstelle ein Test-Quote...")
                
                # Erstelle ein Test-Quote
                from datetime import datetime, timedelta
                test_quote = Quote(
                    project_id=1,
                    milestone_id=1,
                    service_provider_id=153,
                    title="Test Angebot für BuildWise Fee Test",
                    description="Automatisch erstelltes Test-Angebot",
                    status=QuoteStatus.SUBMITTED,
                    total_amount=5000.00,
                    currency="CHF",
                    valid_until=datetime.now() + timedelta(days=30),
                    company_name="Test Firma GmbH",
                    contact_person="Test Person",
                    email="test@example.com",
                    phone="+41 12 345 67 89"
                )
                db.add(test_quote)
                await db.commit()
                await db.refresh(test_quote)
                print(f"   Test-Quote erstellt: ID {test_quote.id}")
            
            print(f"\n2. Test-Quote gefunden:")
            print(f"   - ID: {test_quote.id}")
            print(f"   - Projekt: {test_quote.project_id}")
            print(f"   - Milestone: {test_quote.milestone_id}")
            print(f"   - Status: {test_quote.status}")
            print(f"   - Betrag: {test_quote.total_amount} {test_quote.currency}")
            print(f"   - Service Provider: {test_quote.service_provider_id}")
            
            # Prüfe ob bereits eine Gebühr existiert
            print(f"\n3. Prüfe ob bereits eine BuildWise-Gebühr für Quote {test_quote.id} existiert...")
            existing_fee_result = await db.execute(
                select(BuildWiseFee).where(BuildWiseFee.quote_id == test_quote.id)
            )
            existing_fee = existing_fee_result.scalar_one_or_none()
            
            if existing_fee:
                print(f"   HINWEIS: Gebühr existiert bereits (ID: {existing_fee.id})")
                print(f"   Dies ist normal wenn der Test bereits vorher gelaufen ist")
                return
            else:
                print(f"   OK: Keine Gebühr vorhanden, kann neu erstellt werden")
            
            # Akzeptiere das Quote
            print(f"\n4. Akzeptiere Quote {test_quote.id}...")
            print("-" * 80)
            
            accepted_quote = await accept_quote(db, test_quote.id)
            
            print("-" * 80)
            
            if not accepted_quote:
                print("   FEHLER: Quote konnte nicht akzeptiert werden")
                return
            
            print(f"\n5. Quote erfolgreich akzeptiert!")
            print(f"   - Status: {accepted_quote.status}")
            print(f"   - Accepted At: {accepted_quote.accepted_at}")
            
            # Prüfe ob BuildWise-Gebühr erstellt wurde
            print(f"\n6. Prüfe ob BuildWise-Gebühr erstellt wurde...")
            fee_result = await db.execute(
                select(BuildWiseFee).where(BuildWiseFee.quote_id == test_quote.id)
            )
            created_fee = fee_result.scalar_one_or_none()
            
            if created_fee:
                print("\n" + "="*80)
                print("ERFOLG: BUILDWISE-GEBUEHR WURDE AUTOMATISCH ERSTELLT!")
                print("="*80)
                print(f"   Fee ID: {created_fee.id}")
                print(f"   Rechnungsnummer: {created_fee.invoice_number}")
                print(f"   Nettobetrag: {created_fee.fee_amount} {created_fee.currency}")
                print(f"   Bruttobetrag: {created_fee.gross_amount} {created_fee.currency}")
                print(f"   Provisionssatz: {created_fee.fee_percentage}%")
                print(f"   Rechnungsdatum: {created_fee.invoice_date}")
                print(f"   Faelligkeitsdatum: {created_fee.due_date}")
                print(f"   Status: {created_fee.status}")
                print("="*80)
                print("\nTEST BESTANDEN!")
            else:
                print("\n" + "="*80)
                print("FEHLER: KEINE BUILDWISE-GEBUEHR ERSTELLT!")
                print("="*80)
                print("   Das Quote wurde akzeptiert, aber die BuildWise-Gebühr wurde nicht erstellt.")
                print("   Überprüfen Sie die Backend-Logs für Details.")
                print("\nTEST FEHLGESCHLAGEN!")
            
        except Exception as e:
            print(f"\nFEHLER: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
            raise
    
    await engine.dispose()

if __name__ == "__main__":
    print("Starte Test: Quote Accept mit automatischer BuildWise-Gebuehr...")
    asyncio.run(test_accept_new_quote())



