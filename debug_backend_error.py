import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from app.core.config import get_settings
from app.models.quote import Quote, QuoteStatus
from app.models.cost_position import CostPosition
from app.services.cost_position_service import get_cost_positions_from_accepted_quotes

async def debug_backend_error():
    """Debug-Skript um den Backend-Fehler zu reproduzieren"""
    settings = get_settings()
    
    # Datenbankverbindung
    database_url = f"sqlite+aiosqlite:///{settings.db_name}"
    engine = create_async_engine(database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print("🔍 Debug: Reproduziere Backend-Fehler...")
        
        try:
            # Teste die problematische Funktion
            print("📋 Teste get_cost_positions_from_accepted_quotes für Projekt 4...")
            cost_positions = await get_cost_positions_from_accepted_quotes(db, 4)
            print(f"✅ Erfolgreich: {len(cost_positions)} Kostenpositionen gefunden")
            
        except Exception as e:
            print(f"❌ Fehler reproduziert: {e}")
            print(f"📋 Fehler-Typ: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            
            # Zusätzliche Diagnose
            print("\n🔍 Zusätzliche Diagnose:")
            
            # Teste Import von func
            try:
                from sqlalchemy import func
                print("✅ func Import erfolgreich")
            except ImportError as ie:
                print(f"❌ func Import fehlgeschlagen: {ie}")
            
            # Teste QuoteStatus
            try:
                print(f"✅ QuoteStatus.ACCEPTED: {QuoteStatus.ACCEPTED}")
            except AttributeError as ae:
                print(f"❌ QuoteStatus.ACCEPTED nicht gefunden: {ae}")
                print(f"📋 Verfügbare QuoteStatus: {[s.name for s in QuoteStatus]}")

async def main():
    await debug_backend_error()

if __name__ == "__main__":
    asyncio.run(main()) 