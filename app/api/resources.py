from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, date, timedelta
import json

from ..core.database import get_db
from ..api.deps import get_current_user, get_current_user_optional
from ..models import (
    User, Resource, ResourceStatus, ResourceVisibility, 
    ResourceAllocation, AllocationStatus, ResourceRequest, RequestStatus,
    ResourceCalendarEntry, CalendarEntryStatus, ResourceKPIs,
    Milestone, Quote, QuoteStatus, ServiceProviderRatingAggregate
)
from pydantic import BaseModel, Field
from decimal import Decimal


# ============================================
# Pydantic Models (DTOs)
# ============================================

class ResourceBase(BaseModel):
    service_provider_id: int
    project_id: Optional[int] = None
    start_date: datetime
    end_date: datetime
    title: Optional[str] = None
    person_count: int = 1
    daily_hours: Optional[float] = 8.0
    category: str
    subcategory: Optional[str] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = "Deutschland"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: ResourceStatus = ResourceStatus.AVAILABLE
    visibility: ResourceVisibility = ResourceVisibility.PUBLIC
    hourly_rate: Optional[float] = None
    daily_rate: Optional[float] = None
    currency: str = "EUR"
    description: Optional[str] = None
    skills: Optional[List[str]] = None
    equipment: Optional[List[str]] = None
    
    # Bauträger-Zeitraum (gewünschter Zeitraum des Bauträgers)
    builder_preferred_start_date: Optional[datetime] = None
    builder_preferred_end_date: Optional[datetime] = None
    builder_date_range_notes: Optional[str] = None


class ResourceCreate(ResourceBase):
    pass


class ResourceUpdate(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    title: Optional[str] = None
    person_count: Optional[int] = None
    daily_hours: Optional[float] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: Optional[ResourceStatus] = None
    visibility: Optional[ResourceVisibility] = None
    hourly_rate: Optional[float] = None
    daily_rate: Optional[float] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    skills: Optional[List[str]] = None
    equipment: Optional[List[str]] = None
    
    # Bauträger-Zeitraum (gewünschter Zeitraum des Bauträgers)
    builder_preferred_start_date: Optional[datetime] = None
    builder_preferred_end_date: Optional[datetime] = None
    builder_date_range_notes: Optional[str] = None


class ResourceResponse(ResourceBase):
    id: int
    total_hours: Optional[float] = None
    provider_name: Optional[str] = None
    provider_email: Optional[str] = None
    active_allocations: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    # Erweiterte Dienstleister-Details
    provider_phone: Optional[str] = None
    provider_company_name: Optional[str] = None
    provider_company_address: Optional[str] = None
    provider_company_phone: Optional[str] = None
    provider_company_website: Optional[str] = None
    provider_business_license: Optional[str] = None
    provider_bio: Optional[str] = None
    provider_region: Optional[str] = None
    provider_languages: Optional[str] = None
    
    # Bewertungen
    overall_rating: Optional[float] = None
    rating_count: Optional[int] = None

    class Config:
        from_attributes = True


class ResourceAllocationBase(BaseModel):
    resource_id: int
    trade_id: int
    quote_id: Optional[int] = None
    allocated_person_count: int
    allocated_start_date: datetime
    allocated_end_date: datetime
    allocated_hours: Optional[float] = None
    allocation_status: AllocationStatus = AllocationStatus.PRE_SELECTED
    agreed_hourly_rate: Optional[float] = None
    agreed_daily_rate: Optional[float] = None
    total_cost: Optional[float] = None
    notes: Optional[str] = None
    priority: Optional[int] = 5


class ResourceAllocationCreate(ResourceAllocationBase):
    pass


class ResourceAllocationUpdate(BaseModel):
    allocated_person_count: Optional[int] = None
    allocated_start_date: Optional[datetime] = None
    allocated_end_date: Optional[datetime] = None
    allocated_hours: Optional[float] = None
    allocation_status: Optional[AllocationStatus] = None
    agreed_hourly_rate: Optional[float] = None
    agreed_daily_rate: Optional[float] = None
    total_cost: Optional[float] = None
    notes: Optional[str] = None
    priority: Optional[int] = None
    rejection_reason: Optional[str] = None


class ResourceAllocationResponse(ResourceAllocationBase):
    id: int
    invitation_sent_at: Optional[datetime] = None
    invitation_viewed_at: Optional[datetime] = None
    offer_requested_at: Optional[datetime] = None
    offer_submitted_at: Optional[datetime] = None
    decision_made_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


class ResourceSearchParams(BaseModel):
    category: Optional[str] = None
    subcategory: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_persons: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[int] = None
    max_hourly_rate: Optional[float] = None
    skills: Optional[List[str]] = None
    equipment: Optional[List[str]] = None
    status: Optional[ResourceStatus] = None
    service_provider_id: Optional[int] = None
    project_id: Optional[int] = None


class ResourceKPIsResponse(BaseModel):
    service_provider_id: int
    calculation_date: datetime
    total_resources_available: int
    total_resources_allocated: int
    total_resources_completed: int
    total_person_days_available: int
    total_person_days_allocated: int
    total_person_days_completed: int
    utilization_rate: Optional[float] = None
    average_hourly_rate: Optional[float] = None
    total_revenue: Optional[float] = None
    period_start: datetime
    period_end: datetime

    class Config:
        from_attributes = True


# ============================================
# Helper Functions
# ============================================

async def enrich_resource_with_provider_details(resource: Resource, db: AsyncSession) -> dict:
    """Erweitert eine Resource um vollständige Provider-Details und Bewertungen"""
    from ..models import User
    
    # Lade Service Provider direkt aus der Datenbank
    provider_query = select(User).where(User.id == resource.service_provider_id)
    provider_result = await db.execute(provider_query)
    provider = provider_result.scalar_one_or_none()
    
    resource_dict = {
        "id": resource.id,
        "service_provider_id": resource.service_provider_id,
        "project_id": resource.project_id,
        "start_date": resource.start_date,
        "end_date": resource.end_date,
        "title": resource.title,
        "person_count": resource.person_count,
        "daily_hours": resource.daily_hours,
        "total_hours": resource.total_hours,
        "category": resource.category,
        "subcategory": resource.subcategory,
        "address_street": resource.address_street,
        "address_city": resource.address_city,
        "address_postal_code": resource.address_postal_code,
        "address_country": resource.address_country,
        "latitude": resource.latitude,
        "longitude": resource.longitude,
        "status": resource.status,
        "visibility": resource.visibility,
        "hourly_rate": resource.hourly_rate,
        "daily_rate": resource.daily_rate,
        "currency": resource.currency,
        "description": resource.description,
        "skills": resource.skills,
        "equipment": resource.equipment,
        "provider_name": resource.provider_name,
        "provider_email": resource.provider_email,
        "active_allocations": resource.active_allocations,
        "created_at": resource.created_at,
        "updated_at": resource.updated_at,
        # Bauträger-Zeitraum (gewünschter Zeitraum des Bauträgers)
        "builder_preferred_start_date": resource.builder_preferred_start_date,
        "builder_preferred_end_date": resource.builder_preferred_end_date,
        "builder_date_range_notes": resource.builder_date_range_notes,
    }
    
    # Erweiterte Provider-Details hinzufügen
    if provider:
        resource_dict.update({
            "provider_phone": provider.phone,
            "provider_company_name": provider.company_name,
            "provider_company_address": provider.company_address,
            "provider_company_phone": provider.company_phone,
            "provider_company_website": provider.company_website,
            "provider_business_license": provider.business_license,
            "provider_bio": provider.bio,
            "provider_region": provider.region,
            "provider_languages": provider.languages,
        })
    
    # Bewertungsdaten hinzufügen
    try:
        # Lade aggregierte Bewertungsdaten aus der service_provider_rating_aggregates Tabelle
        aggregate_query = select(ServiceProviderRatingAggregate).where(
            ServiceProviderRatingAggregate.service_provider_id == resource.service_provider_id
        )
        
        aggregate_result = await db.execute(aggregate_query)
        aggregate = aggregate_result.scalar_one_or_none()
        
        if aggregate and aggregate.total_ratings > 0:
            # Debug-Log für Bewertungsdaten
            print(f"🔍 DEBUG - Service Provider {resource.service_provider_id}:")
            print(f"   Gesamtbewertung: {aggregate.avg_overall_rating}")
            print(f"   Anzahl Bewertungen: {aggregate.total_ratings}")
            print(f"   Qualität: {aggregate.avg_quality_rating}")
            print(f"   Termintreue: {aggregate.avg_timeliness_rating}")
            print(f"   Kommunikation: {aggregate.avg_communication_rating}")
            print(f"   Preis-Leistung: {aggregate.avg_value_rating}")
            
            resource_dict.update({
                "overall_rating": float(aggregate.avg_overall_rating),
                "rating_count": aggregate.total_ratings,
                # Detaillierte Bewertungskategorien
                "avg_quality_rating": float(aggregate.avg_quality_rating),
                "avg_timeliness_rating": float(aggregate.avg_timeliness_rating),
                "avg_communication_rating": float(aggregate.avg_communication_rating),
                "avg_value_rating": float(aggregate.avg_value_rating)
            })
        else:
            resource_dict.update({
                "overall_rating": None,
                "rating_count": 0,
                "avg_quality_rating": None,
                "avg_timeliness_rating": None,
                "avg_communication_rating": None,
                "avg_value_rating": None
            })
    except Exception as e:
        # Bei Fehlern setze Bewertungen auf None/0
        resource_dict.update({
            "overall_rating": None,
            "rating_count": 0,
            "avg_quality_rating": None,
            "avg_timeliness_rating": None,
            "avg_communication_rating": None,
            "avg_value_rating": None
        })
    
    return resource_dict


# ============================================
# API Router
# ============================================

router = APIRouter(prefix="/resources", tags=["resources"])


# ============================================
# Resources CRUD
# ============================================

@router.post("/", response_model=ResourceResponse)
async def create_resource(
    resource_data: ResourceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Neue Ressource erstellen"""
    
    # Überprüfe dass der aktuelle User der Service Provider ist
    if current_user.id != resource_data.service_provider_id and current_user.user_role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sie können nur Ressourcen für sich selbst erstellen"
        )
    
    # Berechne total_hours
    if resource_data.start_date and resource_data.end_date:
        days_diff = (resource_data.end_date - resource_data.start_date).days + 1
        total_hours = days_diff * (resource_data.daily_hours or 8.0) * resource_data.person_count
    else:
        total_hours = None
    
    # Hole Provider-Informationen
    provider_query = select(User).where(User.id == resource_data.service_provider_id)
    provider_result = await db.execute(provider_query)
    provider = provider_result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service Provider nicht gefunden"
        )
    
    # Erstelle Resource-Objekt mit erweiterten Provider-Details
    resource = Resource(
        **resource_data.model_dump(),
        total_hours=total_hours,
        provider_name=f"{provider.first_name} {provider.last_name}",
        provider_email=provider.email
    )
    
    db.add(resource)
    await db.commit()
    await db.refresh(resource)
    
    # Lade Provider-Details für die Response
    await db.refresh(resource, ['service_provider'])
    
    # Erweitere Resource um Provider-Details
    enriched_resource = await enrich_resource_with_provider_details(resource, db)
    
    return enriched_resource


@router.get("/", response_model=List[ResourceResponse])
async def list_resources(
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_persons: Optional[int] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: Optional[int] = None,
    max_hourly_rate: Optional[float] = None,
    skills: Optional[str] = None,  # Comma-separated
    equipment: Optional[str] = None,  # Comma-separated
    status: Optional[ResourceStatus] = None,
    service_provider_id: Optional[int] = None,
    project_id: Optional[int] = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Liste alle Ressourcen mit optionalen Filtern"""
    
    query = select(Resource).options(selectinload(Resource.service_provider))
    
    # Filter anwenden
    conditions = []
    
    if category:
        conditions.append(Resource.category == category)
    
    if subcategory:
        conditions.append(Resource.subcategory == subcategory)
    
    if start_date:
        conditions.append(Resource.start_date >= start_date)
    
    if end_date:
        conditions.append(Resource.end_date <= end_date)
    
    if min_persons:
        conditions.append(Resource.person_count >= min_persons)
    
    if max_hourly_rate:
        conditions.append(or_(
            Resource.hourly_rate.is_(None),
            Resource.hourly_rate <= max_hourly_rate
        ))
    
    if status:
        conditions.append(Resource.status == status)
    
    if service_provider_id:
        conditions.append(Resource.service_provider_id == service_provider_id)
    
    if project_id:
        conditions.append(Resource.project_id == project_id)
    
    # Skills-Filter
    if skills:
        skill_list = [s.strip() for s in skills.split(",")]
        # SQLite JSON-Suche
        for skill in skill_list:
            conditions.append(Resource.skills.contains([skill]))
    
    # Equipment-Filter
    if equipment:
        equipment_list = [e.strip() for e in equipment.split(",")]
        for equip in equipment_list:
            conditions.append(Resource.equipment.contains([equip]))
    
    # Geo-Filter (vereinfacht für SQLite)
    if latitude and longitude and radius_km:
        # Vereinfachte Geo-Suche (für Production sollte PostGIS verwendet werden)
        lat_range = radius_km * 0.009  # Ungefähre Umrechnung
        lng_range = radius_km * 0.009
        conditions.extend([
            Resource.latitude.between(latitude - lat_range, latitude + lat_range),
            Resource.longitude.between(longitude - lng_range, longitude + lng_range)
        ])
    
    # Sichtbarkeitsfilter
    if current_user and current_user.user_role != "ADMIN":
        conditions.append(or_(
            Resource.visibility == ResourceVisibility.PUBLIC,
            Resource.service_provider_id == current_user.id
        ))
    else:
        # Wenn kein User authentifiziert ist, nur öffentliche Ressourcen anzeigen
        conditions.append(Resource.visibility == ResourceVisibility.PUBLIC)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(Resource.created_at.desc())
    
    result = await db.execute(query)
    resources = result.scalars().all()
    
    # Erweitere Resources um Provider-Details
    enriched_resources = []
    for resource in resources:
        enriched_resource = await enrich_resource_with_provider_details(resource, db)
        enriched_resources.append(enriched_resource)
    
    return enriched_resources


@router.get("/my", response_model=List[ResourceResponse])
async def get_my_resources(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Hole alle Ressourcen des aktuellen Service Providers"""
    
    query = select(Resource).options(selectinload(Resource.service_provider)).where(
        Resource.service_provider_id == current_user.id
    ).order_by(Resource.created_at.desc())
    
    result = await db.execute(query)
    resources = result.scalars().all()
    
    # Erweitere Resources um Provider-Details
    enriched_resources = []
    for resource in resources:
        enriched_resource = await enrich_resource_with_provider_details(resource, db)
        enriched_resources.append(enriched_resource)
    
    return enriched_resources


@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Hole eine spezifische Ressource"""
    
    query = select(Resource).options(selectinload(Resource.service_provider)).where(Resource.id == resource_id)
    result = await db.execute(query)
    resource = result.scalar_one_or_none()
    
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ressource nicht gefunden"
        )
    
    # Sichtbarkeitsprüfung
    if (resource.visibility != ResourceVisibility.PUBLIC and 
        resource.service_provider_id != current_user.id and 
        current_user.user_role != "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diese Ressource"
        )
    
    # Erweitere Resource um Provider-Details
    enriched_resource = await enrich_resource_with_provider_details(resource, db)
    
    return enriched_resource


@router.put("/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: int,
    resource_update: ResourceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Ressource aktualisieren"""
    
    # Hole die Ressource
    query = select(Resource).where(Resource.id == resource_id)
    result = await db.execute(query)
    resource = result.scalar_one_or_none()
    
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ressource nicht gefunden"
        )
    
    # Update-Daten anwenden
    update_data = resource_update.model_dump(exclude_unset=True)
    
    # Prüfe welche Felder aktualisiert werden sollen
    builder_preferred_fields = {
        'builder_preferred_start_date', 
        'builder_preferred_end_date', 
        'builder_date_range_notes'
    }
    other_fields = set(update_data.keys()) - builder_preferred_fields
    
    # Berechtigungsprüfung: 
    # - Service Provider oder Admin können alle Felder aktualisieren
    # - Andere User können nur builder_preferred_* Felder aktualisieren
    if resource.service_provider_id != current_user.id and current_user.user_role != "ADMIN":
        if other_fields:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Keine Berechtigung für diese Ressource-Felder. Nur Service Provider oder Admin können alle Felder aktualisieren."
            )
        # Nur builder_preferred Felder sind erlaubt für andere User
        update_data = {k: v for k, v in update_data.items() if k in builder_preferred_fields}
    
    for field, value in update_data.items():
        setattr(resource, field, value)
    
    # Total Hours neu berechnen falls Zeitraum oder Personen geändert wurden
    if any(field in update_data for field in ['start_date', 'end_date', 'daily_hours', 'person_count']):
        if resource.start_date and resource.end_date:
            days_diff = (resource.end_date - resource.start_date).days + 1
            resource.total_hours = days_diff * (resource.daily_hours or 8.0) * resource.person_count
    
    await db.commit()
    await db.refresh(resource)
    
    # Lade Provider-Details für die Response
    await db.refresh(resource, ['service_provider'])
    
    # Erweitere Resource um Provider-Details
    enriched_resource = await enrich_resource_with_provider_details(resource, db)
    
    return enriched_resource


@router.delete("/{resource_id}")
async def delete_resource(
    resource_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Ressource löschen"""
    
    # Hole die Ressource
    query = select(Resource).where(Resource.id == resource_id)
    result = await db.execute(query)
    resource = result.scalar_one_or_none()
    
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ressource nicht gefunden"
        )
    
    # Berechtigungsprüfung
    if resource.service_provider_id != current_user.id and current_user.user_role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diese Ressource"
        )
    
    # Prüfe ob noch aktive Allokationen existieren
    allocation_query = select(ResourceAllocation).where(
        and_(
            ResourceAllocation.resource_id == resource_id,
            ResourceAllocation.allocation_status.in_([
                AllocationStatus.ACCEPTED,
                AllocationStatus.OFFER_SUBMITTED,
                AllocationStatus.INVITED
            ])
        )
    )
    allocation_result = await db.execute(allocation_query)
    active_allocations = allocation_result.scalars().all()
    
    if active_allocations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ressource kann nicht gelöscht werden - es existieren noch aktive Zuweisungen"
        )
    
    await db.delete(resource)
    await db.commit()
    
    return {"message": "Ressource erfolgreich gelöscht"}


# ============================================
# Geo-Search für Ressourcen
# ============================================

@router.post("/search/geo", response_model=List[ResourceResponse])
async def search_resources_geo(
    search_params: ResourceSearchParams,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Geo-basierte Suche nach Ressourcen"""
    
    query = select(Resource).options(selectinload(Resource.service_provider))
    
    conditions = []
    
    # Standard-Filter
    if search_params.category:
        conditions.append(Resource.category == search_params.category)
    
    if search_params.subcategory:
        conditions.append(Resource.subcategory == search_params.subcategory)
    
    if search_params.start_date:
        conditions.append(Resource.start_date >= search_params.start_date)
    
    if search_params.end_date:
        conditions.append(Resource.end_date <= search_params.end_date)
    
    if search_params.min_persons:
        conditions.append(Resource.person_count >= search_params.min_persons)
    
    if search_params.max_hourly_rate:
        conditions.append(or_(
            Resource.hourly_rate.is_(None),
            Resource.hourly_rate <= search_params.max_hourly_rate
        ))
    
    if search_params.status:
        conditions.append(Resource.status == search_params.status)
    
    # Sichtbarkeitsfilter
    if current_user and current_user.user_role != "ADMIN":
        conditions.append(or_(
            Resource.visibility == ResourceVisibility.PUBLIC,
            Resource.service_provider_id == current_user.id
        ))
    else:
        # Wenn kein User authentifiziert ist, nur öffentliche Ressourcen anzeigen
        conditions.append(Resource.visibility == ResourceVisibility.PUBLIC)
    
    # Geo-Filter
    if (search_params.latitude and search_params.longitude and search_params.radius_km):
        lat_range = search_params.radius_km * 0.009
        lng_range = search_params.radius_km * 0.009
        conditions.extend([
            Resource.latitude.between(
                search_params.latitude - lat_range, 
                search_params.latitude + lat_range
            ),
            Resource.longitude.between(
                search_params.longitude - lng_range, 
                search_params.longitude + lng_range
            )
        ])
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(Resource.created_at.desc()).limit(100)
    
    result = await db.execute(query)
    resources = result.scalars().all()
    
    # Erweitere Resources um Provider-Details
    enriched_resources = []
    for resource in resources:
        enriched_resource = await enrich_resource_with_provider_details(resource, db)
        enriched_resources.append(enriched_resource)
    
    return enriched_resources


# ============================================
# KPIs und Statistiken
# ============================================

@router.get("/kpis", response_model=ResourceKPIsResponse)
async def get_resource_kpis(
    service_provider_id: Optional[int] = None,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Hole KPIs für Ressourcenmanagement"""
    
    # Default auf aktuellen User wenn nicht spezifiziert
    target_provider_id = service_provider_id or current_user.id
    
    # Berechtigungsprüfung
    if target_provider_id != current_user.id and current_user.user_role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diese KPIs"
        )
    
    # Default Zeitraum: letzten 30 Tage
    if not period_start:
        period_start = datetime.now().replace(day=1)  # Monatsanfang
    if not period_end:
        period_end = datetime.now()
    
    # Berechne KPIs
    resource_query = select(Resource).where(
        and_(
            Resource.service_provider_id == target_provider_id,
            Resource.created_at >= period_start,
            Resource.created_at <= period_end
        )
    )
    
    resource_result = await db.execute(resource_query)
    resources = resource_result.scalars().all()
    
    total_resources_available = len([r for r in resources if r.status == ResourceStatus.AVAILABLE])
    total_resources_allocated = len([r for r in resources if r.status == ResourceStatus.ALLOCATED])
    total_resources_completed = len([r for r in resources if r.status == ResourceStatus.COMPLETED])
    
    total_person_days_available = sum(
        ((r.end_date - r.start_date).days + 1) * r.person_count 
        for r in resources if r.status == ResourceStatus.AVAILABLE
    )
    
    total_person_days_allocated = sum(
        ((r.end_date - r.start_date).days + 1) * r.person_count 
        for r in resources if r.status == ResourceStatus.ALLOCATED
    )
    
    total_person_days_completed = sum(
        ((r.end_date - r.start_date).days + 1) * r.person_count 
        for r in resources if r.status == ResourceStatus.COMPLETED
    )
    
    utilization_rate = (
        (total_person_days_allocated + total_person_days_completed) / 
        max(total_person_days_available + total_person_days_allocated + total_person_days_completed, 1)
    ) * 100 if (total_person_days_available + total_person_days_allocated + total_person_days_completed) > 0 else 0
    
    # Durchschnittlicher Stundensatz
    hourly_rates = [r.hourly_rate for r in resources if r.hourly_rate]
    average_hourly_rate = sum(hourly_rates) / len(hourly_rates) if hourly_rates else None
    
    # Geschätzter Umsatz (vereinfacht)
    total_revenue = sum(
        (r.hourly_rate or 0) * (r.total_hours or 0) 
        for r in resources if r.status in [ResourceStatus.ALLOCATED, ResourceStatus.COMPLETED] and r.hourly_rate
    )
    
    return ResourceKPIsResponse(
        service_provider_id=target_provider_id,
        calculation_date=datetime.now(),
        total_resources_available=total_resources_available,
        total_resources_allocated=total_resources_allocated,
        total_resources_completed=total_resources_completed,
        total_person_days_available=total_person_days_available,
        total_person_days_allocated=total_person_days_allocated,
        total_person_days_completed=total_person_days_completed,
        utilization_rate=utilization_rate,
        average_hourly_rate=average_hourly_rate,
        total_revenue=total_revenue,
        period_start=period_start,
        period_end=period_end
    )


@router.get("/statistics", response_model=dict)
async def get_resource_statistics(
    service_provider_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Hole Ressourcen-Statistiken"""
    
    target_provider_id = service_provider_id or current_user.id
    
    if target_provider_id != current_user.id and current_user.user_role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diese Statistiken"
        )
    
    # Basis-Statistiken
    total_resources_query = select(func.count(Resource.id)).where(
        Resource.service_provider_id == target_provider_id
    )
    total_resources_result = await db.execute(total_resources_query)
    total_resources = total_resources_result.scalar()
    
    # Nach Status gruppiert
    status_stats = {}
    for status in ResourceStatus:
        status_query = select(func.count(Resource.id)).where(
            and_(
                Resource.service_provider_id == target_provider_id,
                Resource.status == status
            )
        )
        status_result = await db.execute(status_query)
        status_stats[status.value] = status_result.scalar()
    
    # Nach Kategorie gruppiert
    category_query = select(
        Resource.category, 
        func.count(Resource.id).label('count')
    ).where(
        Resource.service_provider_id == target_provider_id
    ).group_by(Resource.category)
    
    category_result = await db.execute(category_query)
    category_stats = {row.category: row.count for row in category_result.all()}
    
    return {
        "total_resources": total_resources,
        "by_status": status_stats,
        "by_category": category_stats,
        "provider_id": target_provider_id
    }


@router.get("/kpis/detailed", response_model=dict)
async def get_detailed_resource_kpis(
    service_provider_id: Optional[int] = None,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Hole detaillierte KPIs für Ressourcenmanagement Dashboard"""
    
    target_provider_id = service_provider_id or current_user.id
    
    if target_provider_id != current_user.id and current_user.user_role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diese KPIs"
        )
    
    # Default Zeitraum: letzten 6 Monate
    if not period_start:
        period_start = datetime.now().replace(day=1) - timedelta(days=180)
    if not period_end:
        period_end = datetime.now()
    
    # Hole alle Ressourcen des Service Providers
    resources_query = select(Resource).where(
        Resource.service_provider_id == target_provider_id
    )
    resources_result = await db.execute(resources_query)
    resources = resources_result.scalars().all()
    
    # Hole alle Allokationen für diese Ressourcen
    resource_ids = [r.id for r in resources]
    allocations_query = select(ResourceAllocation).where(
        ResourceAllocation.resource_id.in_(resource_ids)
    )
    allocations_result = await db.execute(allocations_query)
    allocations = allocations_result.scalars().all()
    
    # Basis-KPIs berechnen
    total_resources = len(resources)
    available_resources = len([r for r in resources if r.status == ResourceStatus.AVAILABLE])
    allocated_resources = len([r for r in resources if r.status == ResourceStatus.ALLOCATED])
    completed_resources = len([r for r in resources if r.status == ResourceStatus.COMPLETED])
    
    # Personentage berechnen
    total_person_days = sum(
        ((r.end_date - r.start_date).days + 1) * r.person_count 
        for r in resources if r.start_date and r.end_date
    )
    
    allocated_person_days = sum(
        ((r.end_date - r.start_date).days + 1) * r.person_count 
        for r in resources if r.status in [ResourceStatus.ALLOCATED, ResourceStatus.COMPLETED] and r.start_date and r.end_date
    )
    
    # Auslastungsgrad
    utilization_rate = (allocated_person_days / total_person_days * 100) if total_person_days > 0 else 0
    
    # Durchschnittlicher Stundensatz
    hourly_rates = [r.hourly_rate for r in resources if r.hourly_rate]
    average_hourly_rate = sum(hourly_rates) / len(hourly_rates) if hourly_rates else 0
    
    # Geschätzter Umsatz
    total_revenue = sum(
        (r.hourly_rate or 0) * (r.total_hours or 0) 
        for r in resources if r.status in [ResourceStatus.ALLOCATED, ResourceStatus.COMPLETED] and r.hourly_rate
    )
    
    # Angebotsquote berechnen
    total_allocations = len(allocations)
    submitted_offers = len([a for a in allocations if a.allocation_status == AllocationStatus.OFFER_SUBMITTED])
    offer_rate = (submitted_offers / total_allocations * 100) if total_allocations > 0 else 0
    
    # Durchschnittliche Antwortzeit (in Stunden)
    response_times = []
    for allocation in allocations:
        if allocation.invitation_sent_at and allocation.offer_submitted_at:
            response_time = (allocation.offer_submitted_at - allocation.invitation_sent_at).total_seconds() / 3600
            response_times.append(response_time)
    
    average_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    # Kategorie-Performance
    category_performance = {}
    for resource in resources:
        category = resource.category
        if category not in category_performance:
            category_performance[category] = {
                'total': 0,
                'allocated': 0,
                'revenue': 0,
                'person_days': 0
            }
        
        category_performance[category]['total'] += 1
        if resource.status in [ResourceStatus.ALLOCATED, ResourceStatus.COMPLETED]:
            category_performance[category]['allocated'] += 1
            category_performance[category]['revenue'] += (resource.hourly_rate or 0) * (resource.total_hours or 0)
        
        if resource.start_date and resource.end_date:
            days = (resource.end_date - resource.start_date).days + 1
            category_performance[category]['person_days'] += days * resource.person_count
    
    # Geografische Verteilung
    geographic_distribution = {}
    for resource in resources:
        city = resource.address_city or 'Unbekannt'
        if city not in geographic_distribution:
            geographic_distribution[city] = 0
        geographic_distribution[city] += 1
    
    # Zeitliche Entwicklung (letzte 6 Monate)
    monthly_stats = {}
    current_date = period_start
    while current_date <= period_end:
        month_key = current_date.strftime('%Y-%m')
        monthly_resources = [r for r in resources if r.created_at.strftime('%Y-%m') == month_key]
        monthly_allocations = [a for a in allocations if a.created_at.strftime('%Y-%m') == month_key]
        
        monthly_stats[month_key] = {
            'resources_created': len(monthly_resources),
            'allocations_created': len(monthly_allocations),
            'revenue': sum((r.hourly_rate or 0) * (r.total_hours or 0) for r in monthly_resources if r.status in [ResourceStatus.ALLOCATED, ResourceStatus.COMPLETED])
        }
        
        # Nächster Monat
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    return {
        "overview": {
            "total_resources": total_resources,
            "available_resources": available_resources,
            "allocated_resources": allocated_resources,
            "completed_resources": completed_resources,
            "total_person_days": total_person_days,
            "allocated_person_days": allocated_person_days,
            "utilization_rate": round(utilization_rate, 2),
            "average_hourly_rate": round(average_hourly_rate, 2),
            "total_revenue": round(total_revenue, 2),
            "offer_rate": round(offer_rate, 2),
            "average_response_time": round(average_response_time, 2)
        },
        "category_performance": category_performance,
        "geographic_distribution": geographic_distribution,
        "monthly_trends": monthly_stats,
        "period": {
            "start": period_start.isoformat(),
            "end": period_end.isoformat()
        },
        "provider_id": target_provider_id
    }


# ============================================
# Resource Allocations CRUD
# ============================================

@router.post("/allocations", response_model=ResourceAllocationResponse)
async def create_allocation(
    allocation_data: ResourceAllocationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Neue Ressourcen-Zuweisung erstellen"""
    
    # Hole die Ressource um service_provider_id zu bekommen
    resource_query = select(Resource).where(Resource.id == allocation_data.resource_id)
    resource_result = await db.execute(resource_query)
    resource = resource_result.scalar_one_or_none()
    
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ressource mit ID {allocation_data.resource_id} nicht gefunden"
        )
    
    # Erstelle ResourceAllocation-Objekt
    allocation = ResourceAllocation(
        **allocation_data.model_dump(),
        created_by=current_user.id
    )
    
    db.add(allocation)
    await db.commit()
    await db.refresh(allocation)
    
    print(f"[SUCCESS] Allocation erstellt: ID={allocation.id}, Resource={allocation.resource_id}, Trade={allocation.trade_id}, Status={allocation.allocation_status.value if allocation.allocation_status else 'None'}")
    
    # Benachrichtigung senden wenn Status pre_selected ist
    from ..services.notification_service import NotificationService
    
    try:
        if allocation.allocation_status == AllocationStatus.PRE_SELECTED:
            print(f"[INFO] Erstelle Benachrichtigung für Allocation {allocation.id}, Service Provider {resource.service_provider_id}")
            # Ressource wurde einer Ausschreibung zugeordnet
            await NotificationService.create_resource_allocated_notification(
                db=db,
                allocation_id=allocation.id,
                service_provider_id=resource.service_provider_id
            )
            print(f"[SUCCESS] Benachrichtigung erfolgreich erstellt für Service Provider {resource.service_provider_id}")
    except Exception as e:
        import traceback
        print(f"[ERROR] Fehler beim Erstellen der Benachrichtigung: {e}")
        print(f"[ERROR] Traceback details omitted due to encoding issues")
        # Fehler nicht weiterwerfen, da die Hauptfunktion erfolgreich war
    
    return allocation


class BulkAllocationsRequest(BaseModel):
    allocations: List[ResourceAllocationCreate]


@router.post("/allocations/bulk", response_model=List[ResourceAllocationResponse])
async def bulk_create_allocations(
    request_data: BulkAllocationsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mehrere Ressourcen-Zuweisungen gleichzeitig erstellen"""
    
    created_allocations = []
    resource_map = {}  # Cache für Ressourcen
    
    for allocation_data in request_data.allocations:
        # Hole Ressource wenn noch nicht im Cache
        if allocation_data.resource_id not in resource_map:
            resource_query = select(Resource).where(Resource.id == allocation_data.resource_id)
            resource_result = await db.execute(resource_query)
            resource = resource_result.scalar_one_or_none()
            
            if not resource:
                print(f"[WARNING] Ressource {allocation_data.resource_id} nicht gefunden - überspringe")
                continue
                
            resource_map[allocation_data.resource_id] = resource
        
        # Erstelle ResourceAllocation-Objekt
        allocation = ResourceAllocation(
            **allocation_data.model_dump(),
            created_by=current_user.id
        )
        
        db.add(allocation)
        created_allocations.append((allocation, resource_map[allocation_data.resource_id]))
    
    await db.commit()
    
    # Refresh all allocations to get their IDs
    for allocation, resource in created_allocations:
        await db.refresh(allocation)
    
    print(f"[SUCCESS] Bulk: {len(created_allocations)} Allocations erstellt")
    
    # Benachrichtigungen senden für alle erstellten Allocations
    from ..services.notification_service import NotificationService
    
    for allocation, resource in created_allocations:
        try:
            if allocation.allocation_status == AllocationStatus.PRE_SELECTED:
                print(f"[INFO] Bulk: Erstelle Benachrichtigung für Allocation {allocation.id}, Service Provider {resource.service_provider_id}")
                await NotificationService.create_resource_allocated_notification(
                    db=db,
                    allocation_id=allocation.id,
                    service_provider_id=resource.service_provider_id
                )
                print(f"[SUCCESS] Bulk: Benachrichtigung erfolgreich erstellt für Service Provider {resource.service_provider_id}")
        except Exception as e:
            import traceback
            print(f"[ERROR] Bulk: Fehler beim Erstellen der Benachrichtigung für Allocation {allocation.id}: {e}")
            print(f"[ERROR] Traceback details omitted due to encoding issues")
    
    # Return nur die Allocations (ohne Resource-Tupel)
    return [alloc for alloc, _ in created_allocations]


@router.get("/allocations/my", response_model=List[ResourceAllocationResponse])
async def get_my_allocations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Hole alle Zuweisungen für die Ressourcen des aktuellen Service Providers"""
    
    # Hole alle Ressourcen des aktuellen Service Providers
    resources_query = select(Resource.id).where(
        Resource.service_provider_id == current_user.id
    )
    resources_result = await db.execute(resources_query)
    resource_ids = [row[0] for row in resources_result.all()]
    
    if not resource_ids:
        return []
    
    # Hole alle Allokationen für diese Ressourcen
    query = select(ResourceAllocation).options(
        selectinload(ResourceAllocation.resource)
    ).where(
        ResourceAllocation.resource_id.in_(resource_ids)
    ).order_by(ResourceAllocation.created_at.desc())
    
    result = await db.execute(query)
    allocations = result.scalars().all()
    
    return allocations


@router.get("/allocations/{allocation_id}", response_model=ResourceAllocationResponse)
async def get_allocation(
    allocation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Hole eine spezifische Ressourcen-Zuweisung"""
    
    query = select(ResourceAllocation).where(ResourceAllocation.id == allocation_id)
    result = await db.execute(query)
    allocation = result.scalar_one_or_none()
    
    if not allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ressourcen-Zuweisung nicht gefunden"
        )
    
    return allocation


@router.put("/allocations/{allocation_id}", response_model=ResourceAllocationResponse)
async def update_allocation(
    allocation_id: int,
    allocation_update: ResourceAllocationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Ressourcen-Zuweisung aktualisieren"""
    
    # Hole die Zuweisung
    query = select(ResourceAllocation).where(ResourceAllocation.id == allocation_id)
    result = await db.execute(query)
    allocation = result.scalar_one_or_none()
    
    if not allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ressourcen-Zuweisung nicht gefunden"
        )
    
    # Update-Daten anwenden
    update_data = allocation_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(allocation, field, value)
    
    await db.commit()
    await db.refresh(allocation)
    
    return allocation


@router.delete("/allocations/{allocation_id}")
async def delete_allocation(
    allocation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Ressourcen-Zuweisung löschen"""
    
    # Hole die Zuweisung
    query = select(ResourceAllocation).where(ResourceAllocation.id == allocation_id)
    result = await db.execute(query)
    allocation = result.scalar_one_or_none()
    
    if not allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ressourcen-Zuweisung nicht gefunden"
        )
    
    await db.delete(allocation)
    await db.commit()
    
    return {"message": "Ressourcen-Zuweisung erfolgreich gelöscht"}


@router.get("/allocations/trade/{trade_id}", response_model=List[ResourceAllocationResponse])
async def get_allocations_by_trade(
    trade_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Hole alle Zuweisungen für ein Gewerk/Trade"""
    
    query = select(ResourceAllocation).where(
        ResourceAllocation.trade_id == trade_id
    ).order_by(ResourceAllocation.priority.asc(), ResourceAllocation.created_at.desc())
    
    result = await db.execute(query)
    allocations = result.scalars().all()
    
    return allocations


@router.get("/allocations/resource/{resource_id}", response_model=List[ResourceAllocationResponse])
async def get_allocations_by_resource(
    resource_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Hole alle Zuweisungen für eine Ressource"""
    
    query = select(ResourceAllocation).where(
        ResourceAllocation.resource_id == resource_id
    ).order_by(ResourceAllocation.created_at.desc())
    
    result = await db.execute(query)
    allocations = result.scalars().all()
    
    return allocations


@router.put("/allocations/{allocation_id}/status", response_model=ResourceAllocationResponse)
async def update_allocation_status(
    allocation_id: int,
    status_update: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Status einer Ressourcen-Zuweisung aktualisieren"""
    
    # Hole die Zuweisung
    query = select(ResourceAllocation).where(ResourceAllocation.id == allocation_id)
    result = await db.execute(query)
    allocation = result.scalar_one_or_none()
    
    if not allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ressourcen-Zuweisung nicht gefunden"
        )
    
    # Status aktualisieren
    new_status = status_update.get('status')
    notes = status_update.get('notes')
    old_status = allocation.allocation_status
    
    if new_status:
        allocation.allocation_status = AllocationStatus(new_status)
    
    if notes:
        allocation.notes = notes
    
    # Timestamps setzen
    if new_status == AllocationStatus.INVITED:
        allocation.invitation_sent_at = datetime.now()
    elif new_status == AllocationStatus.OFFER_REQUESTED:
        allocation.offer_requested_at = datetime.now()
    elif new_status == AllocationStatus.OFFER_SUBMITTED:
        allocation.offer_submitted_at = datetime.now()
    elif new_status in [AllocationStatus.ACCEPTED, AllocationStatus.REJECTED]:
        allocation.decision_made_at = datetime.now()
    
    await db.commit()
    await db.refresh(allocation)
    
    # Benachrichtigungen senden basierend auf Status-Änderung
    from ..services.notification_service import NotificationService
    
    try:
        if new_status == AllocationStatus.PRE_SELECTED and old_status != AllocationStatus.PRE_SELECTED:
            # Ressource wurde einer Ausschreibung zugeordnet
            await NotificationService.create_resource_allocated_notification(
                db=db,
                allocation_id=allocation_id,
                service_provider_id=allocation.resource.service_provider_id
            )
        elif new_status == AllocationStatus.INVITED and old_status != AllocationStatus.INVITED:
            # Einladung zur Angebotsabgabe
            deadline = status_update.get('deadline')
            deadline_dt = datetime.fromisoformat(deadline) if deadline else None
            await NotificationService.create_tender_invitation_notification(
                db=db,
                allocation_id=allocation_id,
                service_provider_id=allocation.resource.service_provider_id,
                deadline=deadline_dt
            )
    except Exception as e:
        print(f"[WARNING] Fehler beim Erstellen der Benachrichtigung: {e}")
        # Fehler nicht weiterwerfen, da die Hauptfunktion erfolgreich war
    
    return allocation


@router.post("/allocations/{allocation_id}/invite")
async def send_invitation_notification(
    allocation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Einladungsbenachrichtigung für eine Ressourcen-Zuweisung senden"""
    
    # Hole die Zuweisung
    query = select(ResourceAllocation).where(ResourceAllocation.id == allocation_id)
    result = await db.execute(query)
    allocation = result.scalar_one_or_none()
    
    if not allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ressourcen-Zuweisung nicht gefunden"
        )
    
    # Status auf "invited" setzen und Timestamp aktualisieren
    allocation.allocation_status = AllocationStatus.INVITED
    allocation.invitation_sent_at = datetime.now()
    
    await db.commit()
    
    # Hier würde normalerweise eine E-Mail oder Push-Benachrichtigung gesendet werden
    # Für jetzt geben wir nur eine Erfolgsmeldung zurück
    
    return {"message": "Einladung wurde erfolgreich versendet"}


@router.get("/allocations/my-pending", response_model=List[ResourceAllocationResponse])
async def get_my_pending_allocations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Hole alle wartenden Ressourcen-Zuweisungen für den aktuellen Dienstleister"""
    
    # Hole alle Ressourcen des aktuellen Service Providers
    resources_query = select(Resource.id).where(
        Resource.service_provider_id == current_user.id
    )
    resources_result = await db.execute(resources_query)
    resource_ids = [row[0] for row in resources_result.all()]
    
    if not resource_ids:
        return []
    
    # Hole alle Allokationen für diese Ressourcen mit Status pre_selected
    query = select(ResourceAllocation).options(
        selectinload(ResourceAllocation.resource),
        selectinload(ResourceAllocation.trade)
    ).where(
        and_(
            ResourceAllocation.resource_id.in_(resource_ids),
            ResourceAllocation.allocation_status == AllocationStatus.PRE_SELECTED
        )
    ).order_by(ResourceAllocation.created_at.desc())
    
    result = await db.execute(query)
    allocations = result.scalars().all()
    
    return allocations


class SubmitQuoteFromAllocationRequest(BaseModel):
    title: str
    description: Optional[str] = None
    labor_cost: Optional[float] = None
    material_cost: Optional[float] = None
    overhead_cost: Optional[float] = None
    total_amount: float
    currency: str = "EUR"
    estimated_duration: Optional[int] = None
    start_date: Optional[datetime] = None
    notes: Optional[str] = None


@router.post("/allocations/{allocation_id}/submit-quote")
async def submit_quote_from_allocation(
    allocation_id: int,
    quote_data: SubmitQuoteFromAllocationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Erstellt ein Angebot aus einer Ressourcen-Zuordnung
    
    - Erstellt ein neues Quote
    - Aktualisiert ResourceAllocation Status auf offer_submitted
    - Aktualisiert Resource Status auf quote_submitted
    - Sendet Benachrichtigung an Bauträger
    """
    
    # Hole die Zuweisung mit allen relevanten Daten
    query = select(ResourceAllocation).options(
        selectinload(ResourceAllocation.resource),
        selectinload(ResourceAllocation.trade)
    ).where(ResourceAllocation.id == allocation_id)
    result = await db.execute(query)
    allocation = result.scalar_one_or_none()
    
    if not allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ressourcen-Zuweisung nicht gefunden"
        )
    
    # Prüfe ob die Ressource dem aktuellen User gehört
    if allocation.resource.service_provider_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diese Ressourcen-Zuweisung"
        )
    
    # Prüfe ob bereits ein Angebot existiert
    if allocation.allocation_status != AllocationStatus.PRE_SELECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Angebot kann nicht erstellt werden. Aktueller Status: {allocation.allocation_status.value}"
        )
    
    try:
        # Erstelle Quote
        new_quote = Quote(
            service_provider_id=current_user.id,
            milestone_id=allocation.trade_id,
            project_id=allocation.trade.project_id if allocation.trade else None,
            title=quote_data.title,
            description=quote_data.description,
            labor_cost=quote_data.labor_cost,
            material_cost=quote_data.material_cost,
            overhead_cost=quote_data.overhead_cost,
            total_amount=quote_data.total_amount,
            currency=quote_data.currency,
            estimated_duration=quote_data.estimated_duration,
            start_date=quote_data.start_date,
            additional_notes=quote_data.notes,
            status=QuoteStatus.SUBMITTED  # Direkt als submitted markieren
        )
        
        db.add(new_quote)
        await db.flush()  # Flush um Quote ID zu erhalten
        
        # Aktualisiere ResourceAllocation
        allocation.allocation_status = AllocationStatus.OFFER_SUBMITTED
        allocation.quote_id = new_quote.id
        allocation.offer_submitted_at = datetime.now()
        allocation.agreed_hourly_rate = allocation.resource.hourly_rate if allocation.resource else None
        allocation.agreed_daily_rate = allocation.resource.daily_rate if allocation.resource else None
        allocation.total_cost = quote_data.total_amount
        
        # Aktualisiere Resource Status
        if allocation.resource:
            allocation.resource.status = ResourceStatus.ALLOCATED  # Markiere als allocated (Angebot abgegeben)
        
        await db.commit()
        await db.refresh(new_quote)
        await db.refresh(allocation)
        
        # Sende Benachrichtigung an Bauträger
        from ..services.notification_service import NotificationService
        try:
            # Hole Bauträger ID vom Projekt
            if allocation.trade and allocation.trade.project_id:
                project_query = select(Project).where(Project.id == allocation.trade.project_id)
                project_result = await db.execute(project_query)
                project = project_result.scalar_one_or_none()
                
                if project and project.owner_id:
                    await NotificationService.create_quote_submitted_notification(
                        db=db,
                        quote_id=new_quote.id,
                        recipient_id=project.owner_id
                    )
                    print(f"[OK] Benachrichtigung an Bauträger gesendet: Quote #{new_quote.id}")
        except Exception as e:
            print(f"[WARN] Fehler beim Senden der Benachrichtigung: {e}")
        
        # Markiere ursprüngliche "resource_allocated" Benachrichtigung als gelesen
        try:
            from ..models.notification import Notification
            notification_query = select(Notification).where(
                Notification.recipient_id == current_user.id,
                Notification.type == 'RESOURCE_ALLOCATED',
                Notification.data.like(f'%"allocation_id": {allocation_id}%')
            )
            notification_result = await db.execute(notification_query)
            resource_notification = notification_result.scalar_one_or_none()
            
            if resource_notification:
                resource_notification.is_acknowledged = True
                resource_notification.acknowledged_at = datetime.now()
                await db.commit()
                print(f"[OK] Ursprüngliche resource_allocated Benachrichtigung als gelesen markiert: ID={resource_notification.id}")
            else:
                print(f"[WARN] Keine resource_allocated Benachrichtigung für Allocation {allocation_id} gefunden")
        except Exception as e:
            print(f"[WARN] Fehler beim Markieren der ursprünglichen Benachrichtigung: {e}")
            # Fehler nicht weiterwerfen, da die Hauptfunktion erfolgreich war
            # Fehler nicht weiterwerfen, da Hauptoperation erfolgreich war
        
        return {
            "message": "Angebot erfolgreich erstellt",
            "quote_id": new_quote.id,
            "allocation_id": allocation.id,
            "status": "offer_submitted"
        }
        
    except Exception as e:
        await db.rollback()
        print(f"[ERROR] Fehler beim Erstellen des Angebots: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Erstellen des Angebots: {str(e)}"
        )


class RejectAllocationRequest(BaseModel):
    rejection_reason: str


@router.post("/allocations/{allocation_id}/reject")
async def reject_allocation(
    allocation_id: int,
    rejection_data: RejectAllocationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lehnt eine Ressourcen-Zuordnung ab
    
    - Aktualisiert ResourceAllocation Status auf rejected
    - Aktualisiert Resource Status zurück auf available
    - Speichert Ablehnungsgrund
    """
    
    # Hole die Zuweisung mit allen relevanten Daten
    query = select(ResourceAllocation).options(
        selectinload(ResourceAllocation.resource),
        selectinload(ResourceAllocation.trade)
    ).where(ResourceAllocation.id == allocation_id)
    result = await db.execute(query)
    allocation = result.scalar_one_or_none()
    
    if not allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ressourcen-Zuweisung nicht gefunden"
        )
    
    # Prüfe ob die Ressource dem aktuellen User gehört
    if allocation.resource.service_provider_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diese Ressourcen-Zuweisung"
        )
    
    # Prüfe ob noch im pre_selected Status
    if allocation.allocation_status != AllocationStatus.PRE_SELECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ablehnung nicht möglich. Aktueller Status: {allocation.allocation_status.value}"
        )
    
    try:
        # Aktualisiere ResourceAllocation
        allocation.allocation_status = AllocationStatus.REJECTED
        allocation.rejection_reason = rejection_data.rejection_reason
        allocation.decision_made_at = datetime.now()
        
        # Setze Resource Status zurück auf available
        if allocation.resource:
            allocation.resource.status = ResourceStatus.AVAILABLE
        
        await db.commit()
        await db.refresh(allocation)
        
        return {
            "message": "Ressourcen-Zuordnung erfolgreich abgelehnt",
            "allocation_id": allocation.id,
            "status": "rejected"
        }
        
    except Exception as e:
        await db.rollback()
        print(f"[ERROR] Fehler beim Ablehnen der Zuordnung: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Ablehnen: {str(e)}"
        )


@router.post("/allocations/{allocation_id}/view")
async def mark_invitation_viewed(
    allocation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Markiere Einladung als angesehen"""
    
    # Hole die Zuweisung
    query = select(ResourceAllocation).where(ResourceAllocation.id == allocation_id)
    result = await db.execute(query)
    allocation = result.scalar_one_or_none()
    
    if not allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ressourcen-Zuweisung nicht gefunden"
        )
    
    # Timestamp setzen
    allocation.invitation_viewed_at = datetime.now()
    
    await db.commit()
    
    return {"message": "Einladung als angesehen markiert"}