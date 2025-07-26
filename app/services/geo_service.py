"""
Geo-Service für BuildWise
Handhabt Adressvalidierung, Geocoding und Umkreissuche
"""

import asyncio
import aiohttp
import logging
from typing import Optional, Dict, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
import math

from ..models.user import User, UserType
from ..models.project import Project
from ..models.milestone import Milestone
from ..core.config import settings

logger = logging.getLogger(__name__)


class GeoService:
    """Service für geo-basierte Funktionen"""
    
    def __init__(self):
        self.geocoding_api_url = "https://nominatim.openstreetmap.org/search"
        self.reverse_geocoding_url = "https://nominatim.openstreetmap.org/reverse"
        self.session_timeout = 10
        
    async def geocode_address(self, street: str, zip_code: str, city: str, country: str = "Deutschland") -> Optional[Dict]:
        """
        Geocodiert eine Adresse zu Koordinaten
        
        Args:
            street: Straße und Hausnummer
            zip_code: PLZ
            city: Ort
            country: Land
            
        Returns:
            Dict mit latitude, longitude oder None bei Fehler
        """
        try:
            # Erstelle vollständige Adresse
            full_address = f"{street}, {zip_code} {city}, {country}"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.session_timeout)) as session:
                params = {
                    "q": full_address,
                    "format": "json",
                    "limit": 1,
                    "addressdetails": 1,
                    "countrycodes": "de"
                }
                
                async with session.get(self.geocoding_api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data and len(data) > 0:
                            result = data[0]
                            return {
                                "latitude": float(result["lat"]),
                                "longitude": float(result["lon"]),
                                "display_name": result.get("display_name", ""),
                                "address": result.get("address", {}),
                                "confidence": float(result.get("importance", 0))
                            }
                    
            logger.warning(f"Geocoding fehlgeschlagen für Adresse: {full_address}")
            return None
            
        except Exception as e:
            logger.error(f"Fehler beim Geocoding: {str(e)}")
            return None

    async def geocode_address_from_string(self, address_string: str) -> Optional[Dict]:
        """
        Geocodiert eine Adresse aus einem String
        
        Args:
            address_string: Vollständige Adresse als String
            
        Returns:
            Dictionary mit latitude, longitude und display_name oder None
        """
        try:
            logger.info(f"Geocoding Adresse aus String: {address_string}")
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.session_timeout)) as session:
                params = {
                    "q": address_string,
                    "format": "json",
                    "limit": 1,
                    "addressdetails": 1,
                    "countrycodes": "de,ch,at"
                }
                
                async with session.get(self.geocoding_api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data and len(data) > 0:
                            result = data[0]
                            return {
                                "latitude": float(result["lat"]),
                                "longitude": float(result["lon"]),
                                "display_name": result["display_name"],
                                "confidence": float(result.get("importance", 0.5))
                            }
                        else:
                            logger.warning(f"Geocoding fehlgeschlagen für Adresse: {address_string}")
                            return None
                    else:
                        logger.warning(f"Geocoding API-Fehler: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Fehler beim Geocoding: {str(e)}")
            return None

    def parse_address(self, address_string: str) -> Dict[str, str]:
        """
        Parst eine Adresse aus einem String
        
        Args:
            address_string: Vollständige Adresse als String
            
        Returns:
            Dictionary mit street, zip, city
        """
        try:
            # Einfache Adress-Parsing-Logik
            parts = address_string.split(',')
            
            if len(parts) >= 2:
                street = parts[0].strip()
                city_part = parts[1].strip()
                
                # PLZ und Stadt extrahieren
                city_parts = city_part.split()
                if len(city_parts) >= 2 and city_parts[0].isdigit():
                    zip_code = city_parts[0]
                    city = ' '.join(city_parts[1:])
                else:
                    zip_code = ""
                    city = city_part
                
                return {
                    "street": street,
                    "zip": zip_code,
                    "city": city
                }
            else:
                return {
                    "street": address_string,
                    "zip": "",
                    "city": ""
                }
                
        except Exception as e:
            logger.error(f"Fehler beim Adress-Parsing: {str(e)}")
            return {
                "street": address_string,
                "zip": "",
                "city": ""
            }
    
    async def reverse_geocode(self, latitude: float, longitude: float) -> Optional[Dict]:
        """
        Reverse-Geocoding von Koordinaten zu Adresse
        
        Args:
            latitude: Breitengrad
            longitude: Längengrad
            
        Returns:
            Dict mit Adressdaten oder None bei Fehler
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.session_timeout)) as session:
                params = {
                    "lat": latitude,
                    "lon": longitude,
                    "format": "json",
                    "addressdetails": 1,
                    "accept-language": "de"
                }
                
                async with session.get(self.reverse_geocoding_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data and "address" in data:
                            address = data["address"]
                            return {
                                "street": address.get("road", "") + " " + address.get("house_number", ""),
                                "zip_code": address.get("postcode", ""),
                                "city": address.get("city", address.get("town", "")),
                                "country": address.get("country", "Deutschland"),
                                "display_name": data.get("display_name", "")
                            }
                    
            logger.warning(f"Reverse-Geocoding fehlgeschlagen für Koordinaten: {latitude}, {longitude}")
            return None
            
        except Exception as e:
            logger.error(f"Fehler beim Reverse-Geocoding: {str(e)}")
            return None

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Berechnet die Entfernung zwischen zwei Koordinaten (Haversine-Formel)
        
        Args:
            lat1, lon1: Erste Koordinate
            lat2, lon2: Zweite Koordinate
            
        Returns:
            Entfernung in Kilometern
        """
        try:
            # Umrechnung in Radiant
            lat1_rad = math.radians(lat1)
            lon1_rad = math.radians(lon1)
            lat2_rad = math.radians(lat2)
            lon2_rad = math.radians(lon2)
            
            # Haversine-Formel
            dlat = lat2_rad - lat1_rad
            dlon = lon2_rad - lon1_rad
            
            a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            
            # Erdradius in km
            earth_radius = 6371
            
            return earth_radius * c
            
        except Exception as e:
            logger.error(f"Fehler bei der Entfernungsberechnung: {str(e)}")
            return 0.0

    async def search_projects_in_radius(
        self, 
        db: AsyncSession,
        center_lat: float,
        center_lon: float,
        radius_km: float,
        project_type: Optional[str] = None,
        status: Optional[str] = None,
        min_budget: Optional[float] = None,
        max_budget: Optional[float] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Sucht Projekte in einem bestimmten Radius
        
        Args:
            db: Datenbank-Session
            center_lat, center_lon: Zentrum der Suche
            radius_km: Suchradius in km
            project_type: Filter nach Projekttyp
            status: Filter nach Status
            min_budget, max_budget: Budget-Filter
            limit: Maximale Anzahl Ergebnisse
            
        Returns:
            Liste der gefundenen Projekte mit Entfernung
        """
        try:
            # Basis-Query für öffentliche Projekte mit Adressdaten
            query = select(Project).where(
                Project.is_public == True,
                Project.allow_quotes == True,
                Project.address.isnot(None)
            )
            
            # Filter anwenden
            if project_type:
                query = query.where(Project.project_type == project_type)
            if status:
                query = query.where(Project.status == status)
            if min_budget is not None:
                query = query.where(Project.budget >= min_budget)
            if max_budget is not None:
                query = query.where(Project.budget <= max_budget)
            
            result = await db.execute(query)
            projects = result.scalars().all()
            
            # Entfernung berechnen und filtern
            projects_with_distance = []
            for project in projects:
                project_address = getattr(project, 'address', None)
                if project_address and isinstance(project_address, str):
                    # Geocoding für die Adresse durchführen
                    geocoding_result = await self.geocode_address_from_string(project_address)
                    
                    if geocoding_result:
                        distance = self.calculate_distance(
                            center_lat, center_lon,
                            geocoding_result["latitude"], geocoding_result["longitude"]
                        )
                        
                        if distance <= radius_km:
                            # Adresse parsen
                            address_parts = self.parse_address(project_address)
                            
                            project_dict = {
                                "id": project.id,
                                "name": project.name,
                                "description": project.description,
                                "project_type": project.project_type.value,
                                "status": project.status.value,
                                "address_street": address_parts.get("street", ""),
                                "address_zip": address_parts.get("zip", ""),
                                "address_city": address_parts.get("city", ""),
                                "address_latitude": geocoding_result["latitude"],
                                "address_longitude": geocoding_result["longitude"],
                                "budget": project.budget,
                                "distance_km": round(distance, 2),
                                "created_at": project.created_at.isoformat() if project.created_at is not None else None
                            }
                            projects_with_distance.append(project_dict)
            
            # Nach Entfernung sortieren
            projects_with_distance.sort(key=lambda x: x["distance_km"])
            
            return projects_with_distance[:limit]
            
        except Exception as e:
            logger.error(f"Fehler bei der Umkreissuche: {str(e)}")
            return []

    async def search_trades_in_radius(
        self,
        db: AsyncSession,
        center_lat: float,
        center_lon: float,
        radius_km: float,
        category: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        min_budget: Optional[float] = None,
        max_budget: Optional[float] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Sucht Gewerke (Trades) in einem bestimmten Radius - speziell für Dienstleister
        
        Args:
            db: Datenbank-Session
            center_lat, center_lon: Zentrum der Suche
            radius_km: Suchradius in km
            category: Filter nach Gewerk-Kategorie
            status: Filter nach Status
            priority: Filter nach Priorität
            min_budget, max_budget: Budget-Filter
            limit: Maximale Anzahl Ergebnisse
            
        Returns:
            Liste der gefundenen Gewerke mit Entfernung und Projekt-Informationen
        """
        try:
            # Basis-Query für Gewerke mit Projekt-Join - verwende bereits geocodierte Projekte
            # Zeige ALLE Gewerke an (mit und ohne Besichtigungsoption)
            query = select(Milestone, Project).join(
                Project, Milestone.project_id == Project.id
            ).where(
                Project.is_public == True,
                Project.allow_quotes == True,
                Project.address_latitude.isnot(None),
                Project.address_longitude.isnot(None)
            )
            
            # Filter anwenden
            if category:
                query = query.where(Milestone.category == category)
            if status:
                query = query.where(Milestone.status == status)
            if priority:
                query = query.where(Milestone.priority == priority)
            if min_budget is not None:
                query = query.where(Milestone.budget >= min_budget)
            if max_budget is not None:
                query = query.where(Milestone.budget <= max_budget)
            
            result = await db.execute(query)
            milestone_project_pairs = result.all()
            
            # Lade Quote-Statistiken für Badge-System
            from ..models.quote import Quote, QuoteStatus
            quote_stats = {}
            for milestone, _ in milestone_project_pairs:
                quote_result = await db.execute(
                    select(Quote).where(Quote.milestone_id == milestone.id)
                )
                quotes = list(quote_result.scalars().all())
                
                # Berechne Quote-Statistiken mit korrekten Enum-Werten
                total_quotes = len(quotes)
                accepted_quotes = len([q for q in quotes if q.status == QuoteStatus.ACCEPTED])
                pending_quotes = len([q for q in quotes if q.status in [QuoteStatus.SUBMITTED, QuoteStatus.UNDER_REVIEW]])
                rejected_quotes = len([q for q in quotes if q.status == QuoteStatus.REJECTED])
                
                quote_stats[milestone.id] = {
                    "total_quotes": total_quotes,
                    "accepted_quotes": accepted_quotes,
                    "pending_quotes": pending_quotes,
                    "rejected_quotes": rejected_quotes,
                    "has_accepted_quote": accepted_quotes > 0,
                    "has_pending_quotes": pending_quotes > 0,
                    "has_rejected_quotes": rejected_quotes > 0
                }
            
            # Entfernung berechnen und filtern
            trades_with_distance = []
            for milestone, project in milestone_project_pairs:
                # Verwende bereits vorhandene Koordinaten
                if project.address_latitude and project.address_longitude:
                    distance = self.calculate_distance(
                        center_lat, center_lon,
                        project.address_latitude, project.address_longitude
                    )
                    
                    if distance <= radius_km:
                        # Quote-Statistiken für Badge-System
                        stats = quote_stats.get(milestone.id, {
                            "total_quotes": 0,
                            "accepted_quotes": 0,
                            "pending_quotes": 0,
                            "rejected_quotes": 0,
                            "has_accepted_quote": False,
                            "has_pending_quotes": False,
                            "has_rejected_quotes": False
                        })
                        
                        trade_dict = {
                            "id": milestone.id,
                            "title": milestone.title,
                            "description": milestone.description,
                            "category": milestone.category or "Unbekannt",
                            "status": milestone.status,
                            "priority": milestone.priority,
                            "budget": milestone.budget,
                            "planned_date": milestone.planned_date.isoformat() if milestone.planned_date else "",
                            "start_date": milestone.start_date.isoformat() if milestone.start_date else None,
                            "end_date": milestone.end_date.isoformat() if milestone.end_date else None,
                            "progress_percentage": milestone.progress_percentage,
                            "contractor": milestone.contractor,
                            # Besichtigungssystem - Explizit übertragen
                            "requires_inspection": bool(getattr(milestone, 'requires_inspection', False)),
                            # Projekt-Informationen
                            "project_id": project.id,
                            "project_name": project.name,
                            "project_type": project.project_type,
                            "project_status": project.status,
                            # Adress-Informationen (vom übergeordneten Projekt)
                            "address_street": project.address_street or "",
                            "address_zip": project.address_zip or "",
                            "address_city": project.address_city or "",
                            "address_latitude": project.address_latitude,
                            "address_longitude": project.address_longitude,
                            "distance_km": round(distance, 2),
                            "created_at": milestone.created_at.isoformat() if milestone.created_at is not None else None,
                            # Badge-System Daten
                            "quote_stats": stats
                        }
                        trades_with_distance.append(trade_dict)
            
            # Nach Entfernung sortieren
            trades_with_distance.sort(key=lambda x: x["distance_km"])
            
            return trades_with_distance[:limit]
            
        except Exception as e:
            logger.error(f"Fehler bei der Gewerk-Umkreissuche: {str(e)}")
            return []

    async def search_service_providers_in_radius(
        self,
        db: AsyncSession,
        center_lat: float,
        center_lon: float,
        radius_km: float,
        user_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Sucht Dienstleister in einem bestimmten Radius
        
        Args:
            db: Datenbank-Session
            center_lat, center_lon: Zentrum der Suche
            radius_km: Suchradius in km
            user_type: Filter nach Benutzertyp
            limit: Maximale Anzahl Ergebnisse
            
        Returns:
            Liste der gefundenen Dienstleister mit Entfernung
        """
        try:
            # Basis-Query für Dienstleister mit Adressdaten
            query = select(User).where(
                User.user_type == UserType.SERVICE_PROVIDER,
                User.is_active == True,
                User.address_latitude.isnot(None),
                User.address_longitude.isnot(None)
            )
            
            # Filter anwenden
            if user_type:
                query = query.where(User.user_type == user_type)
            
            result = await db.execute(query)
            users = result.scalars().all()
            
            # Entfernung berechnen und filtern
            users_with_distance = []
            for user in users:
                if user.address_latitude and user.address_longitude:
                    distance = self.calculate_distance(
                        center_lat, center_lon,
                        user.address_latitude, user.address_longitude
                    )
                    
                    if distance <= radius_km:
                        user_dict = {
                            "id": user.id,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "company_name": user.company_name,
                            "address_street": user.address_street,
                            "address_zip": user.address_zip,
                            "address_city": user.address_city,
                            "address_latitude": user.address_latitude,
                            "address_longitude": user.address_longitude,
                            "distance_km": round(distance, 2),
                            "is_verified": user.is_verified
                        }
                        users_with_distance.append(user_dict)
            
            # Nach Entfernung sortieren
            users_with_distance.sort(key=lambda x: x["distance_km"])
            
            return users_with_distance[:limit]
            
        except Exception as e:
            logger.error(f"Fehler bei der Dienstleister-Suche: {str(e)}")
            return []

    async def get_project_by_id(self, db: AsyncSession, project_id: int) -> Optional[Project]:
        """
        Holt ein Projekt anhand der ID
        
        Args:
            db: Datenbank-Session
            project_id: Projekt-ID
            
        Returns:
            Projekt oder None
        """
        try:
            result = await db.execute(select(Project).where(Project.id == project_id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Fehler beim Laden des Projekts {project_id}: {str(e)}")
            return None

    async def update_user_geocoding(self, db: AsyncSession, user_id: int) -> bool:
        """
        Aktualisiert die Geocoding-Daten eines Users
        
        Args:
            db: Datenbank-Session
            user_id: User-ID
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # User laden
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                return False
            
            # Geocoding durchführen
            geocoding_result = await self.geocode_address(
                user.address_street,
                user.address_zip,
                user.address_city,
                user.address_country
            )
            
            if geocoding_result:
                user.address_latitude = geocoding_result["latitude"]
                user.address_longitude = geocoding_result["longitude"]
                user.address_geocoded = True
                user.address_geocoding_date = datetime.utcnow()
                
                await db.commit()
                logger.info(f"Geocoding für User {user_id} erfolgreich aktualisiert")
                return True
            else:
                logger.warning(f"Geocoding für User {user_id} fehlgeschlagen")
                return False
                
        except Exception as e:
            logger.error(f"Fehler beim Update der User-Geocoding-Daten: {str(e)}")
            return False

    async def update_project_geocoding(self, db: AsyncSession, project_id: int) -> bool:
        """
        Aktualisiert die Geocoding-Daten eines Projekts
        
        Args:
            db: Datenbank-Session
            project_id: Projekt-ID
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Projekt laden
            project = await self.get_project_by_id(db, project_id)
            if not project:
                return False
            
            project_address = getattr(project, 'address', None)
            if not project_address or not isinstance(project_address, str):
                logger.warning(f"Projekt {project_id} hat keine gültige Adresse")
                return False
            
            # Geocoding durchführen
            geocoding_result = await self.geocode_address_from_string(project_address)
            
            if geocoding_result:
                # Geocoding-Daten im Projekt speichern
                setattr(project, 'address_latitude', geocoding_result["latitude"])
                setattr(project, 'address_longitude', geocoding_result["longitude"])
                setattr(project, 'address_geocoded', True)
                setattr(project, 'address_geocoding_date', datetime.utcnow())
                
                await db.commit()
                logger.info(f"Geocoding für Projekt {project_id} erfolgreich aktualisiert")
                return True
            else:
                logger.warning(f"Geocoding für Projekt {project_id} fehlgeschlagen")
                return False
                
        except Exception as e:
            logger.error(f"Fehler beim Update der Projekt-Geocoding-Daten: {str(e)}")
            return False


# Singleton-Instanz
geo_service = GeoService() 