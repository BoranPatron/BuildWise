#!/usr/bin/env python3
"""
Migration: Trade Status Tracking für Dienstleister-Ansicht
Erweitert die Datenbank um Status-Tracking für Gewerke und Angebote
"""

import asyncio
import sys
import os
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import text, select, func
from app.core.config import settings
from app.models.milestone import Milestone, MilestoneStatus
from app.models.quote import Quote, QuoteStatus
from app.models.cost_position import CostPosition
from app.models.user import User

async def add_trade_status_tracking():
    """Erweitert die Datenbank um Status-Tracking für Gewerke"""
    
    print("🔧 Migration: Trade Status Tracking")
    print("=" * 50)
    
    # Erstelle Datenbankverbindung
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with engine.begin() as conn:
        async with AsyncSession(conn) as db:
            
            # 1. Prüfe bestehende Struktur
            print("\n1. 📋 Prüfe bestehende Datenbank-Struktur:")
            
            # Prüfe Milestones (Gewerke)
            milestones_result = await db.execute(select(Milestone))
            milestones = milestones_result.scalars().all()
            print(f"   Milestones (Gewerke): {len(milestones)}")
            
            # Prüfe Quotes (Angebote)
            quotes_result = await db.execute(select(Quote))
            quotes = quotes_result.scalars().all()
            print(f"   Quotes (Angebote): {len(quotes)}")
            
            # Prüfe Cost Positions (akzeptierte Angebote)
            cost_positions_result = await db.execute(select(CostPosition))
            cost_positions = cost_positions_result.scalars().all()
            print(f"   Cost Positions (akzeptierte Angebote): {len(cost_positions)}")
            
            # 2. Erstelle Status-Tracking-Tabelle
            print("\n2. 🗄️ Erstelle Status-Tracking-Tabelle:")
            
            create_status_tracking_table = text("""
                CREATE TABLE IF NOT EXISTS trade_status_tracking (
                    id SERIAL PRIMARY KEY,
                    milestone_id INTEGER REFERENCES milestones(id) ON DELETE CASCADE,
                    service_provider_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    quote_id INTEGER REFERENCES quotes(id) ON DELETE CASCADE,
                    status VARCHAR(50) NOT NULL DEFAULT 'available',
                    quote_submitted_at TIMESTAMP,
                    quote_accepted_at TIMESTAMP,
                    quote_rejected_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(milestone_id, service_provider_id)
                );
            """)
            
            await conn.execute(create_status_tracking_table)
            print("   ✅ Status-Tracking-Tabelle erstellt")
            
            # 3. Erstelle Index für Performance
            print("\n3. ⚡ Erstelle Performance-Indizes:")
            
            create_indexes = text("""
                CREATE INDEX IF NOT EXISTS idx_trade_status_milestone ON trade_status_tracking(milestone_id);
                CREATE INDEX IF NOT EXISTS idx_trade_status_provider ON trade_status_tracking(service_provider_id);
                CREATE INDEX IF NOT EXISTS idx_trade_status_quote ON trade_status_tracking(quote_id);
                CREATE INDEX IF NOT EXISTS idx_trade_status_status ON trade_status_tracking(status);
            """)
            
            await conn.execute(create_indexes)
            print("   ✅ Performance-Indizes erstellt")
            
            # 4. Migriere bestehende Daten
            print("\n4. 🔄 Migriere bestehende Daten:")
            
            # Migriere akzeptierte Quotes
            accepted_quotes = [q for q in quotes if q.status == QuoteStatus.ACCEPTED]
            print(f"   Akzeptierte Quotes gefunden: {len(accepted_quotes)}")
            
            for quote in accepted_quotes:
                # Finde zugehörige Cost Position
                cost_position_result = await db.execute(
                    select(CostPosition).where(CostPosition.quote_id == quote.id)
                )
                cost_position = cost_position_result.scalar_one_or_none()
                
                if cost_position and cost_position.milestone_id:
                    # Erstelle Status-Tracking-Eintrag
                    insert_status = text("""
                        INSERT INTO trade_status_tracking 
                        (milestone_id, service_provider_id, quote_id, status, quote_submitted_at, quote_accepted_at)
                        VALUES (:milestone_id, :service_provider_id, :quote_id, 'accepted', :submitted_at, :accepted_at)
                        ON CONFLICT (milestone_id, service_provider_id) 
                        DO UPDATE SET 
                            status = 'accepted',
                            quote_id = :quote_id,
                            quote_accepted_at = :accepted_at,
                            updated_at = CURRENT_TIMESTAMP
                    """)
                    
                    await conn.execute(insert_status, {
                        'milestone_id': cost_position.milestone_id,
                        'service_provider_id': quote.service_provider_id,
                        'quote_id': quote.id,
                        'submitted_at': quote.submitted_at or quote.created_at,
                        'accepted_at': quote.accepted_at or quote.updated_at
                    })
                    print(f"   ✅ Status für Quote {quote.id} migriert")
            
            # Migriere abgelehnte Quotes
            rejected_quotes = [q for q in quotes if q.status == QuoteStatus.REJECTED]
            print(f"   Abgelehnte Quotes gefunden: {len(rejected_quotes)}")
            
            for quote in rejected_quotes:
                # Finde zugehöriges Milestone über Quote
                milestone_result = await db.execute(
                    select(Milestone).where(Milestone.id == quote.milestone_id)
                )
                milestone = milestone_result.scalar_one_or_none()
                
                if milestone:
                    insert_status = text("""
                        INSERT INTO trade_status_tracking 
                        (milestone_id, service_provider_id, quote_id, status, quote_submitted_at, quote_rejected_at)
                        VALUES (:milestone_id, :service_provider_id, :quote_id, 'rejected', :submitted_at, :rejected_at)
                        ON CONFLICT (milestone_id, service_provider_id) 
                        DO UPDATE SET 
                            status = 'rejected',
                            quote_id = :quote_id,
                            quote_rejected_at = :rejected_at,
                            updated_at = CURRENT_TIMESTAMP
                    """)
                    
                    await conn.execute(insert_status, {
                        'milestone_id': milestone.id,
                        'service_provider_id': quote.service_provider_id,
                        'quote_id': quote.id,
                        'submitted_at': quote.submitted_at or quote.created_at,
                        'rejected_at': quote.updated_at
                    })
                    print(f"   ✅ Status für abgelehnten Quote {quote.id} migriert")
            
            # Migriere eingereichte Quotes
            submitted_quotes = [q for q in quotes if q.status == QuoteStatus.SUBMITTED]
            print(f"   Eingereichte Quotes gefunden: {len(submitted_quotes)}")
            
            for quote in submitted_quotes:
                # Finde zugehöriges Milestone über Quote
                milestone_result = await db.execute(
                    select(Milestone).where(Milestone.id == quote.milestone_id)
                )
                milestone = milestone_result.scalar_one_or_none()
                
                if milestone:
                    insert_status = text("""
                        INSERT INTO trade_status_tracking 
                        (milestone_id, service_provider_id, quote_id, status, quote_submitted_at)
                        VALUES (:milestone_id, :service_provider_id, :quote_id, 'submitted', :submitted_at)
                        ON CONFLICT (milestone_id, service_provider_id) 
                        DO UPDATE SET 
                            status = 'submitted',
                            quote_id = :quote_id,
                            quote_submitted_at = :submitted_at,
                            updated_at = CURRENT_TIMESTAMP
                    """)
                    
                    await conn.execute(insert_status, {
                        'milestone_id': milestone.id,
                        'service_provider_id': quote.service_provider_id,
                        'quote_id': quote.id,
                        'submitted_at': quote.submitted_at or quote.created_at
                    })
                    print(f"   ✅ Status für eingereichten Quote {quote.id} migriert")
            
            # 5. Finale Prüfung
            print("\n5. 📊 Finale Prüfung:")
            
            status_count_result = await db.execute(text("""
                SELECT status, COUNT(*) as count 
                FROM trade_status_tracking 
                GROUP BY status
            """))
            status_counts = status_count_result.fetchall()
            
            print("   Status-Verteilung:")
            for status, count in status_counts:
                print(f"   • {status}: {count}")
            
            total_tracking_result = await db.execute(text("SELECT COUNT(*) FROM trade_status_tracking"))
            total_tracking = total_tracking_result.scalar()
            print(f"   Gesamt: {total_tracking} Status-Tracking-Einträge")
    
    await engine.dispose()
    print("\n✅ Migration abgeschlossen")

if __name__ == "__main__":
    asyncio.run(add_trade_status_tracking()) 