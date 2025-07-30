"""
Geo-basierte API-Endpunkte für BuildWise
Handhabt Umkreissuche, Geocoding und Adressvalidierung
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models.user import User
from ..services.geo_service import geo_service

router = APIRouter(prefix="/geo", tags=["geo"])


class AddressRequest(BaseModel):
    """Request-Model für Adressvalidierung"""
    street: str = Field(..., description="Straße und Hausnummer")
    zip_code: str = Field(..., description="PLZ")
    city: str = Field(..., description="Ort")
    country: str = Field(default="Deutschland", description="Land")


class GeocodingResponse(BaseModel):
    """Response-Model für Geocoding"""
    latitude: float
    longitude: float
    display_name: str
    confidence: float


class LocationRequest(BaseModel):
    """Request-Model für Standort-basierte Suche"""
    latitude: float = Field(..., description="Breitengrad")
    longitude: float = Field(..., description="Längengrad")
    radius_km: float = Field(default=50.0, description="Suchradius in km")


class ProjectSearchRequest(BaseModel):
    """Request-Model für Projekt-Suche"""
    latitude: float = Field(..., description="Breitengrad")
    longitude: float = Field(..., description="Längengrad")
    radius_km: float = Field(default=50.0, description="Suchradius in km")
    project_type: Optional[str] = Field(None, description="Projekttyp-Filter")
    status: Optional[str] = Field(None, description="Status-Filter")
    min_budget: Optional[float] = Field(None, description="Minimales Budget")
    max_budget: Optional[float] = Field(None, description="Maximales Budget")
    limit: int = Field(default=100, description="Maximale Anzahl Ergebnisse")


class TradeSearchRequest(BaseModel):
    """Request-Model für Gewerk-Suche (für Dienstleister)"""
    latitude: float = Field(..., description="Breitengrad")
    longitude: float = Field(..., description="Längengrad")
    radius_km: float = Field(default=50.0, description="Suchradius in km")
    category: Optional[str] = Field(None, description="Gewerk-Kategorie-Filter")
    status: Optional[str] = Field(None, description="Status-Filter")
    priority: Optional[str] = Field(None, description="Prioritäts-Filter")
    min_budget: Optional[float] = Field(None, description="Minimales Budget")
    max_budget: Optional[float] = Field(None, description="Maximales Budget")
    limit: int = Field(default=100, description="Maximale Anzahl Ergebnisse")


class ServiceProviderSearchRequest(BaseModel):
    """Request-Model für Dienstleister-Suche"""
    latitude: float = Field(..., description="Breitengrad")
    longitude: float = Field(..., description="Längengrad")
    radius_km: float = Field(default=50.0, description="Suchradius in km")
    user_type: Optional[str] = Field(None, description="Benutzertyp-Filter")
    limit: int = Field(default=100, description="Maximale Anzahl Ergebnisse")


class ProjectSearchResult(BaseModel):
    """Response-Model für Projekt-Suchergebnisse"""
    id: int
    name: str
    description: Optional[str]
    project_type: str
    status: str
    address_street: str
    address_zip: str
    address_city: str
    address_latitude: float
    address_longitude: float
    budget: Optional[float]
    distance_km: float
    created_at: Optional[str]


class TradeSearchResult(BaseModel):
    """Response-Model für Gewerk-Suchergebnisse (für Dienstleister)"""
    id: int
    title: str
    description: Optional[str]
    category: str
    status: str
    priority: str
    budget: Optional[float]
    planned_date: str
    start_date: Optional[str]
    end_date: Optional[str]
    progress_percentage: int
    contractor: Optional[str]
    # Besichtigungssystem
    requires_inspection: bool = False
    # Dokumente - Geteilte Dokumente für Dienstleister
    documents: Optional[List[Dict[str, Any]]] = []
    # Projekt-Informationen
    project_id: int
    project_name: str
    project_type: str
    project_status: str
    # Adress-Informationen (vom übergeordneten Projekt)
    address_street: str
    address_zip: str
    address_city: str
    address_latitude: float
    address_longitude: float
    distance_km: float
    created_at: Optional[str]


class ServiceProviderSearchResult(BaseModel):
    """Response-Model für Dienstleister-Suchergebnisse"""
    id: int
    first_name: str
    last_name: str
    company_name: Optional[str]
    address_street: str
    address_zip: str
    address_city: str
    address_latitude: float
    address_longitude: float
    distance_km: float
    is_verified: bool


@router.post("/geocode", response_model=GeocodingResponse)
async def geocode_address(
    address: AddressRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Geocodiert eine Adresse zu Koordinaten
    
    Args:
        address: Adressdaten
        
    Returns:
        Geocoding-Ergebnis mit Koordinaten
    """
    try:
        result = await geo_service.geocode_address(
            address.street,
            address.zip_code,
            address.city,
            address.country
        )
        
        if result:
            return GeocodingResponse(
                latitude=result["latitude"],
                longitude=result["longitude"],
                display_name=result["display_name"],
                confidence=result["confidence"]
            )
        else:
            raise HTTPException(
                status_code=404,
                detail="Adresse konnte nicht geocodiert werden"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Geocoding: {str(e)}"
        )


@router.post("/reverse-geocode", response_model=AddressRequest)
async def reverse_geocode(
    location: LocationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Reverse-Geocoding von Koordinaten zu Adresse
    
    Args:
        location: Koordinaten
        
    Returns:
        Adressdaten
    """
    try:
        result = await geo_service.reverse_geocode(
            location.latitude,
            location.longitude
        )
        
        if result:
            return AddressRequest(
                street=result["street"],
                zip_code=result["zip_code"],
                city=result["city"],
                country=result["country"]
            )
        else:
            raise HTTPException(
                status_code=404,
                detail="Koordinaten konnten nicht zu einer Adresse umgewandelt werden"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Reverse-Geocoding: {str(e)}"
        )


@router.post("/search-projects", response_model=List[ProjectSearchResult])
async def search_projects_in_radius(
    search_request: ProjectSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sucht Projekte in einem bestimmten Radius
    
    Args:
        search_request: Suchparameter
        
    Returns:
        Liste der gefundenen Projekte mit Entfernung
    """
    try:
        # Prüfe ob User ein Dienstleister ist (erweiterte Prüfung)
        is_service_provider = (
            current_user.user_type.value == "service_provider" or
            (hasattr(current_user, 'user_role') and current_user.user_role and current_user.user_role.value == "DIENSTLEISTER") or
            (current_user.email and "dienstleister" in current_user.email.lower())
        )
        
        if not is_service_provider:
            raise HTTPException(
                status_code=403,
                detail=f"Nur Dienstleister können nach Projekten suchen. User-Type: {current_user.user_type.value}, User-Role: {getattr(current_user, 'user_role', 'N/A')}, Email: {current_user.email}"
            )
        
        results = await geo_service.search_projects_in_radius(
            db=db,
            center_lat=search_request.latitude,
            center_lon=search_request.longitude,
            radius_km=search_request.radius_km,
            project_type=search_request.project_type,
            status=search_request.status,
            min_budget=search_request.min_budget,
            max_budget=search_request.max_budget,
            limit=search_request.limit
        )
        
        return [ProjectSearchResult(**result) for result in results]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fehler bei der Projekt-Suche: {str(e)}"
        )


@router.post("/search-trades", response_model=List[TradeSearchResult])
async def search_trades_in_radius(
    search_request: TradeSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sucht Gewerke (Trades) in einem bestimmten Radius - speziell für Dienstleister
    
    Args:
        search_request: Suchparameter
        
    Returns:
        Liste der gefundenen Gewerke mit Entfernung und Projekt-Informationen
    """
    try:
        # Prüfe Benutzerrolle (Dienstleister oder Bauträger)
        is_service_provider = (
            current_user.user_type.value == "service_provider" or
            (hasattr(current_user, 'user_role') and current_user.user_role and current_user.user_role.value == "DIENSTLEISTER") or
            (current_user.email and "dienstleister" in current_user.email.lower())
        )
        
        is_bautraeger = (
            current_user.user_type.value == "private" or
            (hasattr(current_user, 'user_role') and current_user.user_role and current_user.user_role.value == "BAUTRAEGER") or
            (current_user.email and "bautraeger" in current_user.email.lower())
        )
        
        if not is_service_provider and not is_bautraeger:
            raise HTTPException(
                status_code=403,
                detail=f"Nur Dienstleister und Bauträger können nach Gewerken suchen. User-Type: {current_user.user_type.value}, User-Role: {getattr(current_user, 'user_role', 'N/A')}, Email: {current_user.email}"
            )
        
        results = await geo_service.search_trades_in_radius(
            db=db,
            center_lat=search_request.latitude,
            center_lon=search_request.longitude,
            radius_km=search_request.radius_km,
            category=search_request.category,
            status=search_request.status,
            priority=search_request.priority,
            min_budget=search_request.min_budget,
            max_budget=search_request.max_budget,
            limit=search_request.limit,
            current_user=current_user,  # User für Filterung übergeben
            is_service_provider=is_service_provider
        )
        
        return [TradeSearchResult(**result) for result in results]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fehler bei der Gewerk-Suche: {str(e)}"
        )


@router.post("/search-service-providers", response_model=List[ServiceProviderSearchResult])
async def search_service_providers_in_radius(
    search_request: ServiceProviderSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sucht Dienstleister in einem bestimmten Radius
    
    Args:
        search_request: Suchparameter
        
    Returns:
        Liste der gefundenen Dienstleister mit Entfernung
    """
    try:
        results = await geo_service.search_service_providers_in_radius(
            db=db,
            center_lat=search_request.latitude,
            center_lon=search_request.longitude,
            radius_km=search_request.radius_km,
            user_type=search_request.user_type,
            limit=search_request.limit
        )
        
        return [ServiceProviderSearchResult(**result) for result in results]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fehler bei der Dienstleister-Suche: {str(e)}"
        )


@router.post("/update-user-geocoding/{user_id}")
async def update_user_geocoding(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Aktualisiert die Geocoding-Daten eines Users
    
    Args:
        user_id: User-ID
        
    Returns:
        Erfolgsmeldung
    """
    try:
        # Prüfe Berechtigung
        if current_user.id != user_id and current_user.user_type.value != "admin":
            raise HTTPException(
                status_code=403,
                detail="Keine Berechtigung für diese Aktion"
            )
        
        success = await geo_service.update_user_geocoding(db, user_id)
        
        if success:
            return {"message": "Geocoding erfolgreich aktualisiert"}
        else:
            raise HTTPException(
                status_code=404,
                detail="User nicht gefunden oder Geocoding fehlgeschlagen"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Update der Geocoding-Daten: {str(e)}"
        )


@router.post("/update-project-geocoding/{project_id}")
async def update_project_geocoding(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Aktualisiert die Geocoding-Daten eines Projekts
    
    Args:
        project_id: Projekt-ID
        
    Returns:
        Erfolgsmeldung
    """
    try:
        # Prüfe Berechtigung
        project = await geo_service.get_project_by_id(db, project_id)
        if not project:
            raise HTTPException(
                status_code=404,
                detail="Projekt nicht gefunden"
            )
        
        if project.owner_id != current_user.id and current_user.user_type.value != "admin":
            raise HTTPException(
                status_code=403,
                detail="Keine Berechtigung für dieses Projekt"
            )
        
        success = await geo_service.update_project_geocoding(db, project_id)
        
        if success:
            return {"message": "Projekt-Geocoding erfolgreich aktualisiert"}
        else:
            raise HTTPException(
                status_code=500,
                detail="Geocoding fehlgeschlagen"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Update der Projekt-Geocoding-Daten: {str(e)}"
        )


@router.get("/get-current-location")
async def get_current_location(
    current_user: User = Depends(get_current_user)
):
    """
    Gibt die aktuellen Geocoding-Daten des Users zurück
    
    Args:
        current_user: Aktueller User
        
    Returns:
        Geocoding-Daten des Users
    """
    try:
        if current_user.address_latitude and current_user.address_longitude:
            return {
                "latitude": current_user.address_latitude,
                "longitude": current_user.address_longitude,
                "address": {
                    "street": current_user.address_street,
                    "zip_code": current_user.address_zip,
                    "city": current_user.address_city,
                    "country": current_user.address_country
                },
                "geocoded": current_user.address_geocoded,
                "geocoding_date": current_user.address_geocoding_date.isoformat() if current_user.address_geocoding_date else None
            }
        else:
            return {
                "latitude": None,
                "longitude": None,
                "address": {
                    "street": current_user.address_street,
                    "zip_code": current_user.address_zip,
                    "city": current_user.address_city,
                    "country": current_user.address_country
                },
                "geocoded": False,
                "geocoding_date": None
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Abrufen der Standortdaten: {str(e)}"
        ) 