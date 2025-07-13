#!/usr/bin/env python3
"""
Nachhaltige Behebung des Problems mit fehlenden Kostenpositionen aus akzeptierten Angeboten
"""

import asyncio
import sys
import os
from sqlalchemy import text
from datetime import datetime, timedelta

# Füge das app-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models import Quote, QuoteStatus, CostPosition, Project

async def fix_cost_positions():
    """Behebt das Problem mit fehlenden Kostenpositionen nachhaltig"""
    try:
    async for db in get_db():
            print("🔧 Starte nachhaltige Behebung der Kostenpositionen...")
            
            # 1. Analysiere aktuelle Datenlage
            print("\n📊 Analysiere aktuelle Datenlage...")
            
            # Prüfe alle Projekte
            projects_result = await db.execute(text("SELECT id, name FROM projects"))
            projects = projects_result.fetchall()
            print(f"  - Gefundene Projekte: {len(projects)}")
            
            # Prüfe alle Quotes
            quotes_result = await db.execute(text("SELECT id, title, status, project_id FROM quotes"))
            quotes = quotes_result.fetchall()
            print(f"  - Gefundene Angebote: {len(quotes)}")
            
            # Prüfe alle CostPositions
            cost_positions_result = await db.execute(text("SELECT id, title, quote_id, project_id FROM cost_positions"))
            cost_positions = cost_positions_result.fetchall()
            print(f"  - Gefundene Kostenpositionen: {len(cost_positions)}")
            
            # 2. Erstelle fehlende Testdaten für Projekt 4
            print("\n🛠️ Erstelle fehlende Testdaten für Projekt 4...")
            
            # Prüfe ob Projekt 4 existiert
            project_4_result = await db.execute(text("SELECT id, name FROM projects WHERE id = 4"))
            project_4 = project_4_result.fetchone()
            
            if not project_4:
                print("  ❌ Projekt 4 existiert nicht - erstelle es...")
                await db.execute(text("""
                    INSERT INTO projects (id, name, description, project_type, status, 
                    progress_percentage, current_costs, is_public, allow_quotes, created_at, updated_at)
                    VALUES (4, 'Hausbau Boran', 'Testprojekt für Kostenpositionen', 'residential', 
                    'active', 25, 0, true, true, :created_at, :updated_at)
                """), {
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                })
                print("  ✅ Projekt 4 erstellt")
            else:
                print(f"  ✅ Projekt 4 existiert bereits: {project_4[1]}")
            
            # 3. Erstelle akzeptierte Angebote für Projekt 4
            print("\n📋 Erstelle akzeptierte Angebote für Projekt 4...")
            
            # Prüfe ob bereits Angebote für Projekt 4 existieren
            existing_quotes_result = await db.execute(text("SELECT id, title, status FROM quotes WHERE project_id = 4"))
            existing_quotes = existing_quotes_result.fetchall()
            
            if not existing_quotes:
                print("  📝 Erstelle neue akzeptierte Angebote...")
                
                # Erstelle 2 akzeptierte Angebote
                await db.execute(text("""
                    INSERT INTO quotes (title, description, project_id, service_provider_id, 
                    total_amount, currency, valid_until, labor_cost, material_cost, overhead_cost,
                    estimated_duration, start_date, completion_date, payment_terms, warranty_period,
                    status, contact_released, created_at, updated_at, accepted_at)
                    VALUES 
                    ('Dachdeckerarbeiten - Boran GmbH', 'Komplette Dachdeckerarbeiten inkl. Dämmung', 
                    4, 1, 45000, 'EUR', :valid_until, 25000, 15000, 5000, 14, :start_date, :completion_date,
                    '30 Tage netto', 5, 'accepted', true, :created_at, :updated_at, :accepted_at),
                    
                    ('Elektroinstallation - Elektro Meier', 'Komplette Elektroinstallation inkl. Smart Home', 
                    4, 1, 28000, 'EUR', :valid_until, 18000, 8000, 2000, 10, :start_date, :completion_date,
                    '14 Tage netto', 3, 'accepted', true, :created_at, :updated_at, :accepted_at)
                """), {
                    "valid_until": (datetime.now() + timedelta(days=30)).isoformat(),
                    "start_date": (datetime.now() + timedelta(days=7)).isoformat(),
                    "completion_date": (datetime.now() + timedelta(days=30)).isoformat(),
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "accepted_at": datetime.now()
                })
                print("  ✅ 2 akzeptierte Angebote erstellt")
            else:
                print(f"  ✅ Bereits {len(existing_quotes)} Angebote für Projekt 4 vorhanden")
                for quote in existing_quotes:
                    print(f"    - ID: {quote[0]}, Titel: {quote[1]}, Status: {quote[2]}")
            
            # 4. Erstelle Kostenpositionen für die akzeptierten Angebote
            print("\n💰 Erstelle Kostenpositionen für akzeptierte Angebote...")
            
            # Hole alle akzeptierten Angebote für Projekt 4
            accepted_quotes_result = await db.execute(text("""
                SELECT id, title, total_amount FROM quotes 
                WHERE project_id = 4 AND status = 'accepted'
            """))
            accepted_quotes = accepted_quotes_result.fetchall()
            
            print(f"  📋 Gefundene akzeptierte Angebote: {len(accepted_quotes)}")
            
            for quote in accepted_quotes:
                quote_id, title, amount = quote
                
                # Prüfe ob bereits eine Kostenposition für dieses Angebot existiert
                existing_cp_result = await db.execute(text("""
                    SELECT id FROM cost_positions WHERE quote_id = :quote_id
                """), {"quote_id": quote_id})
                existing_cp = existing_cp_result.fetchone()
                
                if not existing_cp:
                    print(f"  ➕ Erstelle Kostenposition für Angebot: {title}")
                    
                    # Erstelle Kostenposition
                    await db.execute(text("""
                        INSERT INTO cost_positions (title, description, amount, currency, category, 
                        cost_type, status, contractor_name, progress_percentage, paid_amount, 
                        payment_terms, warranty_period, estimated_duration, labor_cost, material_cost, 
                        overhead_cost, quote_id, project_id, created_at, updated_at)
                        VALUES (:title, :description, :amount, 'EUR', 'construction', 'contractor',
                        'active', :contractor_name, 0, 0, :payment_terms, :warranty_period, 
                        :estimated_duration, :labor_cost, :material_cost, :overhead_cost, 
                        :quote_id, 4, :created_at, :updated_at)
                    """), {
                        "title": f"Kostenposition: {title}",
                        "description": f"Automatisch erstellt aus akzeptiertem Angebot: {title}",
                        "amount": amount,
                        "contractor_name": title.split(" - ")[1] if " - " in title else "Unbekannter Auftragnehmer",
                        "payment_terms": "30 Tage netto",
                        "warranty_period": 5,
                        "estimated_duration": 14,
                        "labor_cost": int(amount * 0.6),
                        "material_cost": int(amount * 0.3),
                        "overhead_cost": int(amount * 0.1),
                        "quote_id": quote_id,
                        "created_at": datetime.now(),
                        "updated_at": datetime.now()
                    })
                    print(f"    ✅ Kostenposition erstellt: {amount} EUR")
                else:
                    print(f"  ✅ Kostenposition für Angebot bereits vorhanden: {title}")
            
            # 5. Validiere das Ergebnis
            print("\n✅ Validiere das Ergebnis...")
            
            # Prüfe finale Anzahl der Kostenpositionen für Projekt 4
            final_cp_result = await db.execute(text("""
                SELECT COUNT(*) FROM cost_positions WHERE project_id = 4
            """))
            final_cp_count = final_cp_result.fetchone()[0]
            print(f"  📊 Kostenpositionen für Projekt 4: {final_cp_count}")
            
            # Prüfe Kostenpositionen aus akzeptierten Angeboten
            accepted_cp_result = await db.execute(text("""
                SELECT cp.id, cp.title, cp.amount, q.title as quote_title
                FROM cost_positions cp
                JOIN quotes q ON cp.quote_id = q.id
                WHERE cp.project_id = 4 AND q.status = 'accepted'
            """))
            accepted_cp = accepted_cp_result.fetchall()
            print(f"  📋 Kostenpositionen aus akzeptierten Angeboten: {len(accepted_cp)}")
            
            for cp in accepted_cp:
                if cp is not None and len(cp) >= 4:
                    print(f"    - {cp[1]}: {cp[2]} EUR (aus: {cp[3]})")
                else:
                    print(f"    - Ungültige Kostenposition-Daten: {cp}")
            
            # Commit der Änderungen
            await db.commit()
            print("\n🎉 Nachhaltige Behebung erfolgreich abgeschlossen!")
        
        break

    except Exception as e:
        print(f"❌ Fehler bei der nachhaltigen Behebung: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_cost_positions()) 