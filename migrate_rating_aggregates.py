"""
Migration: Erstelle service_provider_rating_aggregates Tabelle und migriere bestehende Daten
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.service_provider_rating_aggregate import ServiceProviderRatingAggregate
from app.models.service_provider_rating import ServiceProviderRating
from sqlalchemy import select, func


async def create_aggregates_table():
    """Erstellt die service_provider_rating_aggregates Tabelle"""
    
    async with AsyncSessionLocal() as db:
        # Erstelle Tabelle
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS service_provider_rating_aggregates (
                service_provider_id INTEGER PRIMARY KEY,
                total_ratings INTEGER DEFAULT 0 NOT NULL,
                avg_quality_rating FLOAT(3,1) DEFAULT 0.0 NOT NULL,
                avg_timeliness_rating FLOAT(3,1) DEFAULT 0.0 NOT NULL,
                avg_communication_rating FLOAT(3,1) DEFAULT 0.0 NOT NULL,
                avg_value_rating FLOAT(3,1) DEFAULT 0.0 NOT NULL,
                avg_overall_rating FLOAT(3,1) DEFAULT 0.0 NOT NULL,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (service_provider_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))
        
        await db.commit()
        print("[OK] Tabelle service_provider_rating_aggregates erstellt")


async def migrate_existing_ratings():
    """Migriert bestehende Bewertungen zu Aggregat-Tabelle"""
    
    async with AsyncSessionLocal() as db:
        # Hole alle Service Provider mit Bewertungen
        result = await db.execute(
            select(ServiceProviderRating.service_provider_id).distinct()
        )
        service_provider_ids = [row[0] for row in result]
        
        print(f"[INFO] Migriere {len(service_provider_ids)} Service Provider...")
        
        for service_provider_id in service_provider_ids:
            # Berechne Durchschnittswerte
            stats_result = await db.execute(
                select(
                    func.count(ServiceProviderRating.id).label('total_ratings'),
                    func.avg(ServiceProviderRating.quality_rating).label('avg_quality'),
                    func.avg(ServiceProviderRating.timeliness_rating).label('avg_timeliness'),
                    func.avg(ServiceProviderRating.communication_rating).label('avg_communication'),
                    func.avg(ServiceProviderRating.value_rating).label('avg_value'),
                    func.avg(ServiceProviderRating.overall_rating).label('avg_overall')
                ).where(
                    ServiceProviderRating.service_provider_id == service_provider_id,
                    ServiceProviderRating.is_public == 1
                )
            )
            
            stats = stats_result.one()
            
            # Erstelle Aggregat-Eintrag
            aggregate = ServiceProviderRatingAggregate(
                service_provider_id=service_provider_id,
                total_ratings=stats.total_ratings or 0,
                avg_quality_rating=round(stats.avg_quality or 0, 1),
                avg_timeliness_rating=round(stats.avg_timeliness or 0, 1),
                avg_communication_rating=round(stats.avg_communication or 0, 1),
                avg_value_rating=round(stats.avg_value or 0, 1),
                avg_overall_rating=round(stats.avg_overall or 0, 1)
            )
            
            db.add(aggregate)
            print(f"[OK] Service Provider {service_provider_id}: {stats.total_ratings} Bewertungen migriert")
        
        await db.commit()
        print("[SUCCESS] Migration abgeschlossen!")


async def run_migration():
    """Führt die komplette Migration durch"""
    print("[START] Starte Migration für service_provider_rating_aggregates...")
    
    await create_aggregates_table()
    await migrate_existing_ratings()
    
    print("[SUCCESS] Migration erfolgreich abgeschlossen!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_migration())
