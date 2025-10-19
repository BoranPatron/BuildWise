#!/usr/bin/env python3
"""
Manually create BuildWise fee for Quote 1
This script will:
1. Check if Quote 1 is accepted
2. Create a BuildWise fee if it doesn't exist
3. Handle cost_position_id properly
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add app directory to path
sys.path.insert(0, '.')

async def create_fee_for_quote_1():
    """Create BuildWise fee for Quote 1"""
    
    # Create async engine
    DATABASE_URL = "sqlite+aiosqlite:///./buildwise.db"
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            from app.services.buildwise_fee_service import BuildWiseFeeService
            from app.services.quote_service import get_quote_by_id
            from app.models.quote import Quote
            from sqlalchemy import select
            
            print("\n" + "="*80)
            print("PRÜFE QUOTE 1")
            print("="*80)
            
            # Hole Quote 1
            quote_result = await db.execute(select(Quote).where(Quote.id == 1))
            quote = quote_result.scalar_one_or_none()
            
            if not quote:
                print("FEHLER: Quote 1 nicht gefunden")
                return
            
            print(f"OK: Quote gefunden:")
            print(f"   - ID: {quote.id}")
            print(f"   - Projekt: {quote.project_id}")
            print(f"   - Milestone: {quote.milestone_id}")
            print(f"   - Status: {quote.status}")
            print(f"   - Betrag: {quote.total_amount} {quote.currency}")
            print(f"   - Service Provider: {quote.service_provider_id}")
            
            # Prüfe Status
            quote_status = str(quote.status.value).upper() if hasattr(quote.status, 'value') else str(quote.status).upper()
            if quote_status != 'ACCEPTED':
                print(f"FEHLER: Quote ist nicht akzeptiert (Status: {quote_status})")
                return
            
            print(f"OK: Quote ist akzeptiert")
            
            print("\n" + "="*80)
            print("ERSTELLE BUILDWISE GEBUEHR")
            print("="*80)
            
            # Verwende Quote-ID als cost_position_id (wie im Service)
            cost_position_id = quote.id
            
            print(f"Parameter:")
            print(f"   - quote_id: {quote.id}")
            print(f"   - cost_position_id: {cost_position_id} (Quote-ID als Referenz)")
            print(f"   - fee_percentage: None (automatisch aus Konfiguration)")
            
            # Erstelle BuildWise Gebühr
            fee = await BuildWiseFeeService.create_fee_from_quote(
                db=db,
                quote_id=quote.id,
                cost_position_id=cost_position_id,
                fee_percentage=None  # Automatisch aus Konfiguration
            )
            
            print("\nERFOLG: BUILDWISE GEBUEHR ERFOLGREICH ERSTELLT!")
            print(f"   - Fee ID: {fee.id}")
            print(f"   - Rechnungsnummer: {fee.invoice_number}")
            print(f"   - Nettobetrag: {fee.fee_amount} {fee.currency}")
            print(f"   - Bruttobetrag (inkl. MwSt): {fee.gross_amount} {fee.currency}")
            print(f"   - Provisionssatz: {fee.fee_percentage}%")
            print(f"   - Rechnungsdatum: {fee.invoice_date}")
            print(f"   - Faelligkeitsdatum: {fee.due_date}")
            print(f"   - Status: {fee.status}")
            
            print("\n" + "="*80)
            print("FERTIG!")
            print("="*80)
            
        except Exception as e:
            print(f"\nFEHLER: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
            raise
    
    await engine.dispose()

if __name__ == "__main__":
    print("Erstelle BuildWise Gebuehr fuer Quote 1...")
    asyncio.run(create_fee_for_quote_1())

