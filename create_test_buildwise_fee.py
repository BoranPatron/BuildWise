#!/usr/bin/env python3
"""
Test-Skript für BuildWise-Gebühren-Erstellung
"""

import asyncio
import sys
import os
from decimal import Decimal
from datetime import date, timedelta

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from app.models.buildwise_fee import BuildWiseFee, BuildWiseFeeStatus
from app.models.quote import Quote, QuoteStatus
from app.models.cost_position import CostPosition
from app.models.project import Project
from app.models.user import User
from app.schemas.buildwise_fee import BuildWiseFeeCreate
from app.core.config import settings
from sqlalchemy import text, select

async def create_test_buildwise_fee():
    """Erstellt eine Test-BuildWise-Gebühr"""
    
    async with AsyncSessionLocal() as db:
        try:
            print("🔍 Prüfe verfügbare Daten...")
            
            # Prüfe Projekte
            projects = await db.execute(text("SELECT id, name FROM projects"))
            projects = projects.fetchall()
            print(f"📋 Verfügbare Projekte: {len(projects)}")
            for p in projects:
                print(f"  - ID: {p[0]}, Name: {p[1]}")
            
            # Prüfe Angebote
            quotes = await db.execute(text("SELECT id, project_id, service_provider_id, total_amount, status FROM quotes"))
            quotes = quotes.fetchall()
            print(f"📋 Verfügbare Angebote: {len(quotes)}")
            for q in quotes:
                print(f"  - ID: {q[0]}, Project: {q[1]}, Provider: {q[2]}, Amount: {q[3]}, Status: {q[4]}")
            
            # Prüfe Kostenpositionen
            cost_positions = await db.execute(text("SELECT id, project_id, title, amount FROM cost_positions"))
            cost_positions = cost_positions.fetchall()
            print(f"📋 Verfügbare Kostenpositionen: {len(cost_positions)}")
            for cp in cost_positions:
                print(f"  - ID: {cp[0]}, Project: {cp[1]}, Title: {cp[2]}, Amount: {cp[3]}")
            
            # Prüfe Benutzer
            users = await db.execute(text("SELECT id, email, first_name, last_name FROM users"))
            users = users.fetchall()
            print(f"📋 Verfügbare Benutzer: {len(users)}")
            for u in users:
                print(f"  - ID: {u[0]}, Email: {u[1]}, Name: {u[2]} {u[3]}")
            
            # Prüfe bestehende BuildWise-Gebühren
            existing_fees = await db.execute(text("SELECT id, quote_id, cost_position_id, fee_amount FROM buildwise_fees"))
            existing_fees = existing_fees.fetchall()
            print(f"📋 Bestehende BuildWise-Gebühren: {len(existing_fees)}")
            for fee in existing_fees:
                print(f"  - ID: {fee[0]}, Quote: {fee[1]}, CostPosition: {fee[2]}, Amount: {fee[3]}")
            
            # Suche nach akzeptierten Angeboten
            accepted_quotes = [q for q in quotes if q[4] == 'ACCEPTED']
            print(f"✅ Akzeptierte Angebote: {len(accepted_quotes)}")
            
            if not accepted_quotes:
                print("❌ Keine akzeptierten Angebote gefunden!")
                print("💡 Tipp: Akzeptieren Sie zuerst ein Angebot im Frontend")
                return
            
            # Verwende das erste akzeptierte Angebot
            quote = accepted_quotes[0]
            quote_id = quote[0]
            project_id = quote[1]
            service_provider_id = quote[2]
            quote_amount = float(quote[3])
            
            print(f"🎯 Verwende Angebot: ID={quote_id}, Project={project_id}, Amount={quote_amount}")
            
            # Suche passende Kostenposition
            matching_cost_position = None
            for cp in cost_positions:
                if cp[1] == project_id:  # Gleiches Projekt
                    matching_cost_position = cp
                    break
            
            if not matching_cost_position:
                print("❌ Keine passende Kostenposition gefunden!")
                return
            
            cost_position_id = matching_cost_position[0]
            print(f"🎯 Verwende Kostenposition: ID={cost_position_id}, Title={matching_cost_position[2]}")
            
            # Prüfe ob bereits eine Gebühr existiert
            existing_fee = await db.execute(
                text("SELECT id FROM buildwise_fees WHERE quote_id = :quote_id AND cost_position_id = :cost_position_id"),
                {"quote_id": quote_id, "cost_position_id": cost_position_id}
            )
            existing_fee = existing_fee.fetchone()
            
            if existing_fee:
                print(f"⚠️ Bereits eine Gebühr für Quote {quote_id} und CostPosition {cost_position_id} vorhanden")
                return
            
            # Berechne Gebührenbetrag
            fee_percentage = settings.buildwise_fee_percentage
            fee_amount = quote_amount * (fee_percentage / 100.0)
            tax_amount = round(fee_amount * 0.19, 2)
            gross_amount = round(fee_amount * 1.19, 2)
            
            print(f"💰 Gebühren-Berechnung:")
            print(f"  - Angebotsbetrag: {quote_amount} EUR")
            print(f"  - Gebühren-Prozentsatz: {fee_percentage}%")
            print(f"  - Gebührenbetrag: {fee_amount} EUR")
            print(f"  - Steuer (19%): {tax_amount} EUR")
            print(f"  - Bruttobetrag: {gross_amount} EUR")
            
            # Generiere Rechnungsnummer
            last_fee = await db.execute(text("SELECT invoice_number FROM buildwise_fees ORDER BY id DESC LIMIT 1"))
            last_fee = last_fee.fetchone()
            
            if last_fee and last_fee[0]:
                try:
                    last_number = int(last_fee[0].split('-')[-1])
                    invoice_number = f"BW-{str(last_number + 1).zfill(6)}"
                except (ValueError, IndexError):
                    invoice_number = "BW-000001"
            else:
                invoice_number = "BW-000001"
            
            print(f"📄 Rechnungsnummer: {invoice_number}")
            
            # Erstelle die Gebühr direkt als Dictionary
            fee_dict = {
                "project_id": project_id,
                "quote_id": quote_id,
                "cost_position_id": cost_position_id,
                "service_provider_id": service_provider_id,
                "fee_amount": Decimal(str(round(fee_amount, 2))),
                "fee_percentage": Decimal(str(fee_percentage)),
                "quote_amount": Decimal(str(quote_amount)),
                "currency": "EUR",
                "invoice_number": invoice_number,
                "invoice_date": date.today(),
                "due_date": date.today() + timedelta(days=30),
                "status": "open",  # Direkter String-Wert
                "invoice_pdf_path": None,
                "invoice_pdf_generated": False,
                "tax_rate": Decimal("19.0"),
                "tax_amount": Decimal(str(tax_amount)),
                "net_amount": Decimal(str(round(fee_amount, 2))),
                "gross_amount": Decimal(str(gross_amount)),
                "fee_details": f"BuildWise-Gebühr für Angebot {quote_id}",
                "notes": "Test-Gebühr erstellt via Skript"
            }
            
            fee = BuildWiseFee(**fee_dict)
            db.add(fee)
            await db.commit()
            await db.refresh(fee)
            
            print(f"✅ BuildWise-Gebühr erfolgreich erstellt!")
            print(f"  - ID: {fee.id}")
            print(f"  - Rechnungsnummer: {fee.invoice_number}")
            print(f"  - Betrag: {fee.fee_amount} EUR")
            print(f"  - Status: {fee.status}")
            
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der Test-Gebühr: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Erstelle Test-BuildWise-Gebühr...")
    asyncio.run(create_test_buildwise_fee())
    print("✅ Fertig!") 