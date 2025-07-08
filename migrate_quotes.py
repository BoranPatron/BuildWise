#!/usr/bin/env python3
"""
Skript zur Migration der Datenbank: Erweitert die quotes-Tabelle um neue Felder für Dienstleister-Angebote
"""

import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Füge das BuildWise-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def migrate_quotes():
    """Erweitert die quotes-Tabelle um neue Felder"""
    
    # Erstelle Engine für SQLite
    DATABASE_URL = "sqlite+aiosqlite:///./buildwise.db"
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    
    async with engine.begin() as conn:
        print("🔧 Erweitere quotes-Tabelle um neue Felder...")
        
        # Neue Felder für Dienstleister-Angebote
        new_columns = [
            ("milestone_id", "INTEGER REFERENCES milestones(id)"),
            ("company_name", "VARCHAR"),
            ("contact_person", "VARCHAR"),
            ("phone", "VARCHAR"),
            ("email", "VARCHAR"),
            ("website", "VARCHAR"),
            ("pdf_upload_path", "VARCHAR"),
            ("additional_documents", "TEXT"),
            ("rating", "FLOAT"),
            ("feedback", "TEXT")
        ]
        
        for column_name, column_type in new_columns:
            # Prüfe ob die Spalte bereits existiert
            result = await conn.execute(text(f"""
                SELECT name FROM pragma_table_info('quotes') 
                WHERE name = '{column_name}'
            """))
            
            if result.fetchone():
                print(f"✅ Spalte {column_name} existiert bereits")
            else:
                # Füge die Spalte hinzu
                await conn.execute(text(f"""
                    ALTER TABLE quotes 
                    ADD COLUMN {column_name} {column_type}
                """))
                print(f"✅ Spalte {column_name} erfolgreich hinzugefügt")
        
        print("🎉 Migration der quotes-Tabelle erfolgreich abgeschlossen!")


async def create_sample_quotes():
    """Erstellt Beispiel-Angebote für Demonstrationszwecke"""
    
    # Erstelle Engine für SQLite
    DATABASE_URL = "sqlite+aiosqlite:///./buildwise.db"
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    
    async with engine.begin() as conn:
        print("🔧 Erstelle Beispiel-Angebote...")
        
        # Prüfe ob bereits Angebote existieren
        result = await conn.execute(text("SELECT COUNT(*) FROM quotes"))
        count = result.scalar()
        
        if count and count > 0:
            print(f"✅ Bereits {count} Angebote in der Datenbank vorhanden")
            return
        
        # Erstelle Beispiel-Angebote für verschiedene Gewerke
        sample_quotes = [
            {
                "project_id": 1,
                "milestone_id": 1,  # Elektroinstallation
                "service_provider_id": 2,
                "title": "Elektroinstallation - Premium",
                "description": "Komplette Elektroinstallation inkl. Smart Home",
                "status": "submitted",
                "total_amount": 45000.0,
                "currency": "EUR",
                "labor_cost": 25000.0,
                "material_cost": 15000.0,
                "overhead_cost": 5000.0,
                "estimated_duration": 45,
                "start_date": "2024-03-01",
                "completion_date": "2024-04-15",
                "payment_terms": "30 Tage nach Rechnung",
                "warranty_period": 24,
                "company_name": "Elektro Meier GmbH",
                "contact_person": "Hans Meier",
                "phone": "+49 123 456789",
                "email": "hans.meier@elektro-meier.de",
                "website": "www.elektro-meier.de",
                "risk_score": 15.0,
                "price_deviation": -5.0,
                "ai_recommendation": "Empfohlen - Gutes Preis-Leistungs-Verhältnis",
                "submitted_at": "2024-01-15 10:00:00"
            },
            {
                "project_id": 1,
                "milestone_id": 1,  # Elektroinstallation
                "service_provider_id": 3,
                "title": "Elektroinstallation - Standard",
                "description": "Standard Elektroinstallation",
                "status": "submitted",
                "total_amount": 52000.0,
                "currency": "EUR",
                "labor_cost": 30000.0,
                "material_cost": 17000.0,
                "overhead_cost": 5000.0,
                "estimated_duration": 50,
                "start_date": "2024-03-05",
                "completion_date": "2024-04-25",
                "payment_terms": "50% bei Auftrag, Rest bei Fertigstellung",
                "warranty_period": 36,
                "company_name": "Elektro Schmidt & Partner",
                "contact_person": "Klaus Schmidt",
                "phone": "+49 987 654321",
                "email": "klaus.schmidt@elektro-schmidt.de",
                "website": "www.elektro-schmidt.de",
                "risk_score": 25.0,
                "price_deviation": 10.0,
                "ai_recommendation": "Höherer Preis, aber längere Garantie",
                "submitted_at": "2024-01-16 14:30:00"
            },
            {
                "project_id": 1,
                "milestone_id": 1,  # Elektroinstallation
                "service_provider_id": 4,
                "title": "Elektroinstallation - Budget",
                "description": "Günstige Elektroinstallation",
                "status": "submitted",
                "total_amount": 38000.0,
                "currency": "EUR",
                "labor_cost": 20000.0,
                "material_cost": 13000.0,
                "overhead_cost": 5000.0,
                "estimated_duration": 40,
                "start_date": "2024-03-01",
                "completion_date": "2024-04-10",
                "payment_terms": "100% bei Fertigstellung",
                "warranty_period": 24,
                "company_name": "Schnell & Günstig Elektro",
                "contact_person": "Peter Schnell",
                "phone": "+49 555 123456",
                "email": "peter.schnell@schnell-elektro.de",
                "website": "www.schnell-elektro.de",
                "risk_score": 35.0,
                "price_deviation": -20.0,
                "ai_recommendation": "Günstigster Preis, aber höheres Risiko",
                "submitted_at": "2024-01-17 09:15:00"
            }
        ]
        
        for quote_data in sample_quotes:
            await conn.execute(text("""
                INSERT INTO quotes (
                    project_id, milestone_id, service_provider_id, title, description,
                    status, total_amount, currency, labor_cost, material_cost, overhead_cost,
                    estimated_duration, start_date, completion_date, payment_terms, warranty_period,
                    company_name, contact_person, phone, email, website,
                    risk_score, price_deviation, ai_recommendation, submitted_at,
                    created_at, updated_at
                ) VALUES (
                    :project_id, :milestone_id, :service_provider_id, :title, :description,
                    :status, :total_amount, :currency, :labor_cost, :material_cost, :overhead_cost,
                    :estimated_duration, :start_date, :completion_date, :payment_terms, :warranty_period,
                    :company_name, :contact_person, :phone, :email, :website,
                    :risk_score, :price_deviation, :ai_recommendation, :submitted_at,
                    datetime('now'), datetime('now')
                )
            """), quote_data)
        
        print("✅ Beispiel-Angebote erfolgreich erstellt!")


async def main():
    """Hauptfunktion"""
    try:
        await migrate_quotes()
        await create_sample_quotes()
        print("🎉 Migration erfolgreich abgeschlossen!")
    except Exception as e:
        print(f"❌ Fehler bei der Migration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 