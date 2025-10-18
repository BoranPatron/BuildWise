"""
Service für Dienstleister-Bewertungen
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from ..models import ServiceProviderRating, ServiceProviderRatingAggregate, User, Milestone, Quote
from ..schemas.rating import (
    ServiceProviderRatingCreate,
    ServiceProviderRatingResponse,
    ServiceProviderRatingSummary
)
from ..core.exceptions import NotFoundException, ConflictException


class RatingService:
    """Service für Verwaltung von Dienstleister-Bewertungen"""
    
    async def create_rating(
        self,
        db: AsyncSession,
        bautraeger_id: int,
        data: ServiceProviderRatingCreate
    ) -> ServiceProviderRating:
        """Erstellt eine neue Bewertung"""
        
        # Prüfe ob bereits bewertet wurde
        existing = await db.execute(
            select(ServiceProviderRating).where(
                ServiceProviderRating.bautraeger_id == bautraeger_id,
                ServiceProviderRating.service_provider_id == data.service_provider_id,
                ServiceProviderRating.milestone_id == data.milestone_id
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictException("Sie haben diesen Dienstleister für dieses Gewerk bereits bewertet")
        
        # Berechne Durchschnittsbewertung
        overall_rating = (
            data.quality_rating + 
            data.timeliness_rating + 
            data.communication_rating + 
            data.value_rating
        ) / 4
        
        # Erstelle Bewertung
        rating = ServiceProviderRating(
            bautraeger_id=bautraeger_id,
            service_provider_id=data.service_provider_id,
            project_id=data.project_id,
            milestone_id=data.milestone_id,
            quote_id=data.quote_id,
            quality_rating=data.quality_rating,
            timeliness_rating=data.timeliness_rating,
            communication_rating=data.communication_rating,
            value_rating=data.value_rating,
            overall_rating=overall_rating,
            comment=data.comment,
            is_public=data.is_public
        )
        
        db.add(rating)
        
        # Markiere Rechnung als eingesehen (wenn quote_id vorhanden)
        if data.quote_id:
            milestone = await db.get(Milestone, data.milestone_id)
            if milestone:
                milestone.invoice_approved = True
                milestone.invoice_approved_at = func.now()
                milestone.invoice_approved_by = bautraeger_id
        
        await db.commit()
        await db.refresh(rating)
        
        # Aktualisiere aggregierte Bewertungen
        await self._update_service_provider_aggregates(db, data.service_provider_id)
        
        return rating
    
    async def get_rating(
        self,
        db: AsyncSession,
        rating_id: int
    ) -> ServiceProviderRating:
        """Holt eine einzelne Bewertung"""
        
        query = select(ServiceProviderRating).where(
            ServiceProviderRating.id == rating_id
        ).options(
            selectinload(ServiceProviderRating.service_provider),
            selectinload(ServiceProviderRating.bautraeger),
            selectinload(ServiceProviderRating.milestone),
            selectinload(ServiceProviderRating.quote)
        )
        
        result = await db.execute(query)
        rating = result.scalar_one_or_none()
        
        if not rating:
            raise NotFoundException("Bewertung nicht gefunden")
            
        return rating
    
    async def get_service_provider_ratings(
        self,
        db: AsyncSession,
        service_provider_id: int,
        only_public: bool = True
    ) -> List[ServiceProviderRating]:
        """Holt alle Bewertungen für einen Dienstleister"""
        
        query = select(ServiceProviderRating).where(
            ServiceProviderRating.service_provider_id == service_provider_id
        ).options(
            selectinload(ServiceProviderRating.bautraeger),
            selectinload(ServiceProviderRating.project),
            selectinload(ServiceProviderRating.milestone)
        ).order_by(ServiceProviderRating.created_at.desc())
        
        if only_public:
            query = query.where(ServiceProviderRating.is_public == 1)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_service_provider_rating_summary(
        self,
        db: AsyncSession,
        service_provider_id: int
    ) -> ServiceProviderRatingSummary:
        """Berechnet Bewertungszusammenfassung für einen Dienstleister"""
        
        # Aggregierte Statistiken
        result = await db.execute(
            select(
                func.count(ServiceProviderRating.id).label('total_ratings'),
                func.avg(ServiceProviderRating.overall_rating).label('avg_overall'),
                func.avg(ServiceProviderRating.quality_rating).label('avg_quality'),
                func.avg(ServiceProviderRating.timeliness_rating).label('avg_timeliness'),
                func.avg(ServiceProviderRating.communication_rating).label('avg_communication'),
                func.avg(ServiceProviderRating.value_rating).label('avg_value')
            ).where(
                ServiceProviderRating.service_provider_id == service_provider_id,
                ServiceProviderRating.is_public == 1
            )
        )
        
        stats = result.one()
        
        # Bewertungsverteilung
        distribution_result = await db.execute(
            select(
                func.floor(ServiceProviderRating.overall_rating).label('rating'),
                func.count(ServiceProviderRating.id).label('count')
            ).where(
                ServiceProviderRating.service_provider_id == service_provider_id,
                ServiceProviderRating.is_public == 1
            ).group_by(
                func.floor(ServiceProviderRating.overall_rating)
            )
        )
        
        distribution = {int(row.rating): row.count for row in distribution_result}
        
        return ServiceProviderRatingSummary(
            service_provider_id=service_provider_id,
            total_ratings=stats.total_ratings or 0,
            average_overall_rating=round(stats.avg_overall or 0, 1),
            average_quality_rating=round(stats.avg_quality or 0, 1),
            average_timeliness_rating=round(stats.avg_timeliness or 0, 1),
            average_communication_rating=round(stats.avg_communication or 0, 1),
            average_value_rating=round(stats.avg_value or 0, 1),
            rating_distribution=distribution
        )
    
    async def check_invoice_viewable(
        self,
        db: AsyncSession,
        milestone_id: int,
        bautraeger_id: int
    ) -> bool:
        """Prüft ob Rechnung angesehen werden kann (nach Bewertung)"""
        
        # Prüfe ob Bewertung existiert
        rating = await db.execute(
            select(ServiceProviderRating).where(
                ServiceProviderRating.milestone_id == milestone_id,
                ServiceProviderRating.bautraeger_id == bautraeger_id
            )
        )
        
        return rating.scalar_one_or_none() is not None
    
    async def _update_service_provider_aggregates(
        self,
        db: AsyncSession,
        service_provider_id: int
    ):
        """Aktualisiert aggregierte Bewertungen für einen Service Provider (performant)"""
        
        # Berechne Durchschnittswerte direkt in der Datenbank (sehr performant)
        result = await db.execute(
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
        
        stats = result.one()
        
        # Upsert Aggregat-Eintrag (sehr performant)
        existing_aggregate = await db.get(ServiceProviderRatingAggregate, service_provider_id)
        
        if existing_aggregate:
            # Update bestehenden Eintrag
            existing_aggregate.total_ratings = stats.total_ratings or 0
            existing_aggregate.avg_quality_rating = round(stats.avg_quality or 0, 1)
            existing_aggregate.avg_timeliness_rating = round(stats.avg_timeliness or 0, 1)
            existing_aggregate.avg_communication_rating = round(stats.avg_communication or 0, 1)
            existing_aggregate.avg_value_rating = round(stats.avg_value or 0, 1)
            existing_aggregate.avg_overall_rating = round(stats.avg_overall or 0, 1)
            existing_aggregate.last_updated = func.now()
        else:
            # Erstelle neuen Eintrag
            aggregate = ServiceProviderRatingAggregate(
                service_provider_id=service_provider_id,
                total_ratings=stats.total_ratings or 0,
                avg_quality_rating=round(stats.avg_quality or 0, 1),
                avg_timeliness_rating=round(stats.avg_timeliness or 0, 1),
                avg_communication_rating=round(stats.avg_communication or 0, 1),
                avg_value_rating=round(stats.avg_value or 0, 1),
                avg_overall_rating=round(stats.avg_overall or 0, 1),
                last_updated=func.now()
            )
            db.add(aggregate)
        
        await db.commit()
    
    async def get_service_provider_aggregated_rating(
        self,
        db: AsyncSession,
        service_provider_id: int
    ) -> Optional[ServiceProviderRatingAggregate]:
        """Holt aggregierte Bewertung für einen Service Provider (sehr performant)"""
        
        return await db.get(ServiceProviderRatingAggregate, service_provider_id)


# Singleton-Instanz
rating_service = RatingService()