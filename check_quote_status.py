#!/usr/bin/env python3
"""
Prüft den Status eines Angebots
"""

import asyncio
import sys
import os

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from app.models.quote import Quote, QuoteStatus

async def check_quote_status():
    """Prüft den Status des Angebots mit ID 1"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Hole das Angebot
            quote = await db.get(Quote, 1)
            if not quote:
                print("❌ Angebot mit ID 1 nicht gefunden")
                return
            
            print(f"📋 Angebot-Details:")
            print(f"  - ID: {quote.id}")
            print(f"  - Titel: {quote.title}")
            print(f"  - Status: {quote.status}")
            print(f"  - Projekt-ID: {quote.project_id}")
            print(f"  - Service-Provider-ID: {quote.service_provider_id}")
            print(f"  - Gesamtbetrag: {quote.total_amount}")
            print(f"  - Währung: {quote.currency}")
            print(f"  - Gültig bis: {quote.valid_until}")
            
            # Prüfe ob Status "accepted" ist
            if quote.status == QuoteStatus.ACCEPTED:
                print("✅ Angebot ist akzeptiert")
            else:
                print(f"❌ Angebot ist NICHT akzeptiert (Status: {quote.status})")
                print("💡 Tipp: Akzeptieren Sie das Angebot im Frontend")
            
        except Exception as e:
            print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    print("🔍 Prüfe Angebots-Status...")
    asyncio.run(check_quote_status())
    print("✅ Fertig!") 