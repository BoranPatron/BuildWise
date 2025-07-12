#!/usr/bin/env python3
"""
Migrationsskript für BuildWise
Konvertiert alle akzeptierten Angebote (Quotes mit Status 'accepted') in Kostenpositionen.
"""

import sys
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def migrate_accepted_quotes_to_cost_positions():
    """
    Hauptfunktion für die Migration von akzeptierten Angeboten zu Kostenpositionen.
    """
    print("🚀 Starte Migration: Akzeptierte Angebote → Kostenpositionen")
    print("=" * 60)
    
    # Direkte SQLite-Verbindung für Migration
    DATABASE_URL = "sqlite:///./buildwise.db"
    engine = create_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    created_count = 0
    skipped_count = 0
    error_count = 0
    
    try:
        # Alle akzeptierten Angebote laden
        print("📋 Lade alle akzeptierten Angebote...")
        result = db.execute(text("SELECT * FROM quotes WHERE status = 'accepted'"))
        accepted_quotes = result.fetchall()
        print(f"✅ {len(accepted_quotes)} akzeptierte Angebote gefunden")
        
        if not accepted_quotes:
            print("ℹ️ Keine akzeptierten Angebote gefunden. Migration nicht erforderlich.")
            return
        
        print("\n🔄 Starte Konvertierung...")
        
        for i, quote in enumerate(accepted_quotes, 1):
            try:
                quote_id = quote.id
                quote_title = quote.title or f"Angebot {quote_id}"
                
                print(f"\n[{i}/{len(accepted_quotes)}] Prüfe Angebot ID {quote_id}: {quote_title}")
                
                # Prüfe, ob bereits eine Kostenposition für dieses Angebot existiert
                existing_result = db.execute(
                    text("SELECT id FROM cost_positions WHERE quote_id = :quote_id"),
                    {"quote_id": quote_id}
                )
                existing_cost_position = existing_result.fetchone()
                
                if existing_cost_position:
                    print(f"   ⏭️ Kostenposition bereits vorhanden (ID: {existing_cost_position.id}) - überspringe")
                    skipped_count += 1
                    continue
                
                # Erstelle neue Kostenposition basierend auf dem Angebot
                print(f"   ➕ Erstelle neue Kostenposition für Angebot {quote_id}")
                
                # Bereite Daten für die neue Kostenposition vor
                cost_position_data = {
                    "title": quote_title,
                    "description": getattr(quote, "description", "") or "",
                    "amount": quote.total_amount,
                    "currency": getattr(quote, "currency", "EUR") or "EUR",
                    "category": "Dienstleistung",
                    "cost_type": "angebot",
                    "status": "offen",
                    "contractor_name": getattr(quote, "company_name", None),
                    "contractor_contact": getattr(quote, "contact_person", None),
                    "contractor_phone": getattr(quote, "phone", None),
                    "contractor_email": getattr(quote, "email", None),
                    "contractor_website": getattr(quote, "website", None),
                    "progress_percentage": 0,
                    "paid_amount": 0,
                    "payment_terms": getattr(quote, "payment_terms", None),
                    "warranty_period": getattr(quote, "warranty_period", None),
                    "estimated_duration": getattr(quote, "estimated_duration", None),
                    "start_date": getattr(quote, "start_date", None),
                    "completion_date": getattr(quote, "completion_date", None),
                    "labor_cost": getattr(quote, "labor_cost", None),
                    "material_cost": getattr(quote, "material_cost", None),
                    "overhead_cost": getattr(quote, "overhead_cost", None),
                    "risk_score": getattr(quote, "risk_score", None),
                    "price_deviation": getattr(quote, "price_deviation", None),
                    "ai_recommendation": getattr(quote, "ai_recommendation", None),
                    "quote_id": quote_id,
                    "milestone_id": getattr(quote, "milestone_id", None),
                    "project_id": quote.project_id,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
                
                # Entferne None-Werte für SQLite
                cost_position_data = {k: v for k, v in cost_position_data.items() if v is not None}
                
                # Erstelle INSERT-Statement
                columns = ", ".join(cost_position_data.keys())
                placeholders = ", ".join([f":{key}" for key in cost_position_data.keys()])
                
                insert_query = f"""
                INSERT INTO cost_positions ({columns})
                VALUES ({placeholders})
                """
                
                result = db.execute(text(insert_query), cost_position_data)
                db.flush()
                
                # Hole die ID der neu erstellten Kostenposition
                new_id_result = db.execute(text("SELECT last_insert_rowid()"))
                new_id_row = new_id_result.fetchone()
                new_id = new_id_row[0] if new_id_row else None
                
                print(f"   ✅ Kostenposition erstellt (ID: {new_id})")
                created_count += 1
                
            except Exception as e:
                print(f"   ❌ Fehler bei Angebot {quote_id}: {str(e)}")
                error_count += 1
                continue
        
        # Änderungen committen
        print(f"\n💾 Committe Änderungen zur Datenbank...")
        db.commit()
        
        print("\n" + "=" * 60)
        print("🎉 Migration erfolgreich abgeschlossen!")
        print(f"📊 Zusammenfassung:")
        print(f"   ✅ Neue Kostenpositionen erstellt: {created_count}")
        print(f"   ⏭️ Übersprungene (bereits vorhanden): {skipped_count}")
        print(f"   ❌ Fehler: {error_count}")
        print(f"   📋 Gesamt verarbeitet: {len(accepted_quotes)}")
        
        if created_count > 0:
            print(f"\n💡 {created_count} neue Kostenpositionen wurden erstellt und sind jetzt im Finance-Bereich verfügbar.")
        
    except Exception as e:
        print(f"\n❌ Kritischer Fehler bei der Migration: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def main():
    """
    Hauptfunktion mit Fehlerbehandlung.
    """
    try:
        migrate_accepted_quotes_to_cost_positions()
    except KeyboardInterrupt:
        print("\n⚠️ Migration durch Benutzer abgebrochen.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Migration fehlgeschlagen: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 