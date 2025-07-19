#!/usr/bin/env python3
"""
Debug-Skript für Quote-Akzeptierung
"""

import asyncio
import sys
import os

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.services.quote_service import get_quote_by_id, accept_quote
from app.models.quote import QuoteStatus


async def debug_quote_acceptance():
    """Debuggt die Quote-Akzeptierung"""
    print("🔧 Debugge Quote-Akzeptierung...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Prüfe, ob Quote mit ID 1 existiert
            print("🔍 Prüfe Quote mit ID 1...")
            quote = await get_quote_by_id(db, 1)
            if not quote:
                print("❌ Quote mit ID 1 nicht gefunden")
                return
            
            print(f"✅ Quote gefunden: {quote.title} (Status: {quote.status})")
            print(f"   Projekt ID: {quote.project_id}")
            print(f"   Service Provider ID: {quote.service_provider_id}")
            print(f"   Milestone ID: {quote.milestone_id}")
            
            # Teste Akzeptierung
            print("🔧 Teste Akzeptierung...")
            accepted_quote = await accept_quote(db, 1)
            
            if accepted_quote:
                print(f"✅ Quote erfolgreich akzeptiert: {accepted_quote.title}")
                print(f"   Status: {accepted_quote.status}")
                print(f"   Akzeptiert am: {accepted_quote.accepted_at}")
            else:
                print("❌ Quote konnte nicht akzeptiert werden")
                
        except Exception as e:
            print(f"❌ Fehler beim Debuggen: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Hauptfunktion"""
    print("🚀 Starte Quote-Akzeptierung Debug...")
    await debug_quote_acceptance()
    print("✅ Debug abgeschlossen")


if __name__ == "__main__":
    asyncio.run(main()) 