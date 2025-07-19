#!/usr/bin/env python3
"""
Test-Skript für Quote-Akzeptierung nach dem Fix
"""

import asyncio
import sys
import os

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.services.quote_service import accept_quote, get_quote_by_id
from app.models.quote import QuoteStatus


async def test_quote_acceptance():
    """Testet die Quote-Akzeptierung"""
    print("🔧 Teste Quote-Akzeptierung...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Prüfe, ob Quote mit ID 1 existiert
            quote = await get_quote_by_id(db, 1)
            if not quote:
                print("❌ Quote mit ID 1 nicht gefunden")
                return
            
            print(f"✅ Quote gefunden: {quote.title} (Status: {quote.status})")
            
            # Teste Akzeptierung
            accepted_quote = await accept_quote(db, 1)
            
            if accepted_quote:
                print(f"✅ Quote erfolgreich akzeptiert: {accepted_quote.title}")
                print(f"   Status: {accepted_quote.status}")
                print(f"   Akzeptiert am: {accepted_quote.accepted_at}")
            else:
                print("❌ Quote konnte nicht akzeptiert werden")
                
        except Exception as e:
            print(f"❌ Fehler beim Testen: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Hauptfunktion"""
    print("🚀 Starte Quote-Akzeptierung Test...")
    await test_quote_acceptance()
    print("✅ Test abgeschlossen")


if __name__ == "__main__":
    asyncio.run(main()) 