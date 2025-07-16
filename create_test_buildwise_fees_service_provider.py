#!/usr/bin/env python3
"""
Skript zur Erstellung von Test-BuildWise-Fees für Dienstleister
"""

import asyncio
import sys
import os
from datetime import datetime, date

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine

async def create_test_buildwise_fees_service_provider():
    """Erstelle Test-BuildWise-Fees für Dienstleister"""
    try:
        async with engine.begin() as conn:
            # Prüfe ob Service Provider mit ID 2 existiert (Dienstleister)
            user_result = await conn.execute(text("SELECT id FROM users WHERE id = 2"))
            user = user_result.fetchone()
            
            if not user:
                print("❌ Service Provider mit ID 2 nicht gefunden. Erstelle Test-Service-Provider...")
                await conn.execute(text("""
                    INSERT INTO users (id, email, hashed_password, first_name, last_name, user_type, is_active, created_at, updated_at)
                    VALUES (2, 'service@buildwise.de', 'hashed_password', 'Service', 'Provider', 'dienstleister', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """))
            
            # Prüfe ob Projekt mit ID 1 existiert
            project_result = await conn.execute(text("SELECT id FROM projects WHERE id = 1"))
            project = project_result.fetchone()
            
            if not project:
                print("❌ Projekt mit ID 1 nicht gefunden. Erstelle Test-Projekt...")
                await conn.execute(text("""
                    INSERT INTO projects (id, name, description, project_type, status, is_public, allow_quotes, created_at, updated_at)
                    VALUES (1, 'Test Projekt', 'Ein Test-Projekt für BuildWise-Fees', 'residential', 'active', 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """))
            
            # Prüfe ob Quote mit ID 1 existiert
            quote_result = await conn.execute(text("SELECT id FROM quotes WHERE id = 1"))
            quote = quote_result.fetchone()
            
            if not quote:
                print("❌ Quote mit ID 1 nicht gefunden. Erstelle Test-Quote...")
                await conn.execute(text("""
                    INSERT INTO quotes (id, title, description, project_id, service_provider_id, total_amount, currency, status, created_at, updated_at)
                    VALUES (1, 'Test Angebot', 'Ein Test-Angebot für BuildWise-Fees', 1, 2, 15000.00, 'EUR', 'accepted', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """))
            
            # Prüfe ob Cost Position mit ID 1 existiert
            cost_position_result = await conn.execute(text("SELECT id FROM cost_positions WHERE id = 1"))
            cost_position = cost_position_result.fetchone()
            
            if not cost_position:
                print("❌ Cost Position mit ID 1 nicht gefunden. Erstelle Test-Cost-Position...")
                await conn.execute(text("""
                    INSERT INTO cost_positions (id, title, description, amount, currency, category, cost_type, status, project_id, created_at, updated_at)
                    VALUES (1, 'Test Kostenposition', 'Eine Test-Kostenposition für BuildWise-Fees', 15000.00, 'EUR', 'material', 'direct', 'active', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """))
            
            # Erstelle Test-BuildWise-Fees für Dienstleister
            current_date = datetime.now()
            
            # Test-Fee 1 - Aktueller Monat, offen
            await conn.execute(text("""
                INSERT OR REPLACE INTO buildwise_fees (
                    id, project_id, quote_id, cost_position_id, service_provider_id,
                    fee_amount, fee_percentage, quote_amount, currency,
                    invoice_number, invoice_date, due_date, status,
                    invoice_pdf_generated, tax_rate, tax_amount, net_amount, gross_amount,
                    fee_details, notes, created_at, updated_at
                ) VALUES (
                    1, 1, 1, 1, 2,
                    150.00, 1.00, 15000.00, 'EUR',
                    'BW-000001', :invoice_date, :due_date, 'open',
                    0, 19.00, 28.50, 150.00, 178.50,
                    'Vermittlungskosten für akzeptiertes Angebot', 'Test-Gebühr für Dienstleister',
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
            """), {
                "invoice_date": current_date.date(),
                "due_date": date(current_date.year, current_date.month + 1, current_date.day)
            })
            
            # Test-Fee 2 - Vorheriger Monat, bezahlt
            prev_month = current_date.replace(month=current_date.month - 1 if current_date.month > 1 else 12)
            if current_date.month == 1:
                prev_month = prev_month.replace(year=current_date.year - 1)
            
            await conn.execute(text("""
                INSERT OR REPLACE INTO buildwise_fees (
                    id, project_id, quote_id, cost_position_id, service_provider_id,
                    fee_amount, fee_percentage, quote_amount, currency,
                    invoice_number, invoice_date, due_date, payment_date, status,
                    invoice_pdf_generated, tax_rate, tax_amount, net_amount, gross_amount,
                    fee_details, notes, created_at, updated_at
                ) VALUES (
                    2, 1, 1, 1, 2,
                    250.00, 1.00, 25000.00, 'EUR',
                    'BW-000002', :invoice_date, :due_date, :payment_date, 'paid',
                    1, 19.00, 47.50, 250.00, 297.50,
                    'Vermittlungskosten für bezahltes Angebot', 'Test-Gebühr für Dienstleister - bezahlt',
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
            """), {
                "invoice_date": prev_month.date(),
                "due_date": date(prev_month.year, prev_month.month + 1, prev_month.day),
                "payment_date": prev_month.date()
            })
            
            # Test-Fee 3 - Überfällig
            overdue_date = current_date.replace(month=current_date.month - 2 if current_date.month > 2 else 12 - (2 - current_date.month))
            if current_date.month <= 2:
                overdue_date = overdue_date.replace(year=current_date.year - 1)
            
            await conn.execute(text("""
                INSERT OR REPLACE INTO buildwise_fees (
                    id, project_id, quote_id, cost_position_id, service_provider_id,
                    fee_amount, fee_percentage, quote_amount, currency,
                    invoice_number, invoice_date, due_date, status,
                    invoice_pdf_generated, tax_rate, tax_amount, net_amount, gross_amount,
                    fee_details, notes, created_at, updated_at
                ) VALUES (
                    3, 1, 1, 1, 2,
                    300.00, 1.00, 30000.00, 'EUR',
                    'BW-000003', :invoice_date, :due_date, 'overdue',
                    1, 19.00, 57.00, 300.00, 357.00,
                    'Vermittlungskosten für überfälliges Angebot', 'Test-Gebühr für Dienstleister - überfällig',
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
            """), {
                "invoice_date": overdue_date.date(),
                "due_date": date(overdue_date.year, overdue_date.month + 1, overdue_date.day)
            })
            
            # Test-Fee-Items
            await conn.execute(text("""
                INSERT OR REPLACE INTO buildwise_fee_items (
                    id, buildwise_fee_id, quote_id, cost_position_id, quote_amount, fee_amount, 
                    fee_percentage, description, created_at
                ) VALUES (
                    1, 1, 1, 1, 15000.00, 150.00, 1.00, 
                    'Test-Gebühr für akzeptiertes Angebot', CURRENT_TIMESTAMP
                )
            """))
            
            await conn.execute(text("""
                INSERT OR REPLACE INTO buildwise_fee_items (
                    id, buildwise_fee_id, quote_id, cost_position_id, quote_amount, fee_amount, 
                    fee_percentage, description, created_at
                ) VALUES (
                    2, 2, 1, 1, 25000.00, 250.00, 1.00, 
                    'Test-Gebühr für bezahltes Angebot', CURRENT_TIMESTAMP
                )
            """))
            
            await conn.execute(text("""
                INSERT OR REPLACE INTO buildwise_fee_items (
                    id, buildwise_fee_id, quote_id, cost_position_id, quote_amount, fee_amount, 
                    fee_percentage, description, created_at
                ) VALUES (
                    3, 3, 1, 1, 30000.00, 300.00, 1.00, 
                    'Test-Gebühr für überfälliges Angebot', CURRENT_TIMESTAMP
                )
            """))
            
            print("✅ Test-BuildWise-Fees für Dienstleister erfolgreich erstellt!")
            print(f"📊 Erstellt: 3 Gebühren für Service Provider ID 2")
            print("   - BW-000001: Offen (aktueller Monat)")
            print("   - BW-000002: Bezahlt (vorheriger Monat)")
            print("   - BW-000003: Überfällig (2 Monate zurück)")
    
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Test-Daten: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_test_buildwise_fees_service_provider()) 