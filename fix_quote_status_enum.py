#!/usr/bin/env python3
"""
Skript um die Quote-Status-Enum-Werte in der Datenbank zu korrigieren
"""

import asyncio
import sys
import os

# Füge das aktuelle Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from sqlalchemy import text

async def fix_quote_status_enum():
    """Korrigiert die Quote-Status-Enum-Werte in der Datenbank"""
    try:
        async for db in get_db():
            print("🔧 Korrigiere Quote-Status-Enum-Werte...")
            
            # Zuerst alle aktuellen Status-Werte anzeigen
            stmt = text("SELECT id, title, status FROM quotes ORDER BY id")
            result = await db.execute(stmt)
            quotes = result.fetchall()
            
            print(f"📋 Gefundene Quotes: {len(quotes)}")
            for quote in quotes:
                print(f"   ID: {quote.id}, Titel: '{quote.title}', Status: {quote.status}")
            
            # Korrigiere die Status-Werte
            print("\n🔧 Korrigiere Status-Werte...")
            
            # Update-Statements für alle möglichen Status-Werte
            updates = [
                ("UPDATE quotes SET status = 'DRAFT' WHERE status = 'draft'", "draft → DRAFT"),
                ("UPDATE quotes SET status = 'SUBMITTED' WHERE status = 'submitted'", "submitted → SUBMITTED"),
                ("UPDATE quotes SET status = 'UNDER_REVIEW' WHERE status = 'under_review'", "under_review → UNDER_REVIEW"),
                ("UPDATE quotes SET status = 'ACCEPTED' WHERE status = 'accepted'", "accepted → ACCEPTED"),
                ("UPDATE quotes SET status = 'REJECTED' WHERE status = 'rejected'", "rejected → REJECTED"),
                ("UPDATE quotes SET status = 'EXPIRED' WHERE status = 'expired'", "expired → EXPIRED")
            ]
            
            total_updated = 0
            for update_stmt, description in updates:
                try:
                    await db.execute(text(update_stmt))
                    print(f"✅ {description}: Update ausgeführt")
                    total_updated += 1
                except Exception as e:
                    print(f"⚠️ Fehler bei {description}: {e}")
            
            # Commit der Änderungen
            await db.commit()
            print(f"\n✅ Updates abgeschlossen")
            
            # Zeige die korrigierten Werte
            print("\n📋 Korrigierte Quotes:")
            stmt = text("SELECT id, title, status FROM quotes ORDER BY id")
            result = await db.execute(stmt)
            quotes = result.fetchall()
            
            for quote in quotes:
                print(f"   ID: {quote.id}, Titel: '{quote.title}', Status: {quote.status}")
            
            print("\n🎉 Quote-Status-Enum-Korrektur abgeschlossen!")
            print("💡 Starte das Backend neu, um die Änderungen zu übernehmen.")
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_quote_status_enum()) 