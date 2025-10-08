from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from typing import List, Optional
from datetime import datetime
import httpx

from ..models import Project, ProjectStatus, ProjectType
from ..schemas.project import ProjectCreate, ProjectUpdate


async def geocode_address(address: str) -> Optional[dict]:
    """Geocodiert eine Adresse mit OpenStreetMap Nominatim API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": address,
                    "format": "json",
                    "limit": 1,
                    "countrycodes": "de,ch,at"  # Deutschland, Schweiz, Österreich
                },
                headers={"User-Agent": "BuildWise/1.0"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    location = data[0]
                    return {
                        "latitude": float(location["lat"]),
                        "longitude": float(location["lon"]),
                        "display_name": location["display_name"]
                    }
    except Exception as e:
        print(f"[ERROR] Geocodierung fehlgeschlagen für '{address}': {e}")
    
    return None


async def create_project(db: AsyncSession, owner_id: int, project_in: ProjectCreate) -> Project:
    """Erstellt ein neues Projekt mit automatischer Geocodierung"""
    project_data = project_in.dict()
    
    # Erstelle vollständige Adresse aus detaillierten Feldern falls address leer ist
    if not project_data.get("address") and any([
        project_data.get("address_street"),
        project_data.get("address_zip"),
        project_data.get("address_city"),
        project_data.get("address_country")
    ]):
        address_parts = []
        if project_data.get("address_street"):
            address_parts.append(project_data["address_street"])
        if project_data.get("address_zip") and project_data.get("address_city"):
            address_parts.append(f"{project_data['address_zip']} {project_data['address_city']}")
        elif project_data.get("address_city"):
            address_parts.append(project_data["address_city"])
        if project_data.get("address_country"):
            address_parts.append(project_data["address_country"])
        
        if address_parts:
            project_data["address"] = ", ".join(address_parts)
            print(f"[BUILD] Erstelle vollständige Adresse: {project_data['address']}")
    
    # Automatische Geocodierung wenn Adresse vorhanden
    if project_data.get("address") and not project_data.get("address_latitude"):
        print(f"🌍 Geocodiere Adresse: {project_data['address']}")
        geocode_result = await geocode_address(project_data["address"])
        
        if geocode_result:
            project_data.update({
                "address_latitude": geocode_result["latitude"],
                "address_longitude": geocode_result["longitude"],
                "address_geocoded": True,
                "address_geocoding_date": datetime.utcnow()
            })
            print(f"[SUCCESS] Geocodierung erfolgreich: {geocode_result['latitude']}, {geocode_result['longitude']}")
        else:
            print("[WARNING] Geocodierung fehlgeschlagen - Projekt wird ohne Koordinaten erstellt")
    
    project = Project(owner_id=owner_id, **project_data)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def get_projects_for_user(db: AsyncSession, owner_id: int) -> List[Project]:
    result = await db.execute(select(Project).where(Project.owner_id == owner_id))
    return list(result.scalars().all())


async def get_project_by_id(db: AsyncSession, project_id: int) -> Project | None:
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalars().first()


async def update_project(db: AsyncSession, project_id: int, project_update: ProjectUpdate) -> Project | None:
    project = await get_project_by_id(db, project_id)
    if not project:
        return None
    
    update_data = project_update.dict(exclude_unset=True)
    
    # Erstelle vollständige Adresse aus detaillierten Feldern falls address leer ist
    if not update_data.get("address") and any([
        update_data.get("address_street"),
        update_data.get("address_zip"),
        update_data.get("address_city"),
        update_data.get("address_country")
    ]):
        address_parts = []
        if update_data.get("address_street"):
            address_parts.append(update_data["address_street"])
        if update_data.get("address_zip") and update_data.get("address_city"):
            address_parts.append(f"{update_data['address_zip']} {update_data['address_city']}")
        elif update_data.get("address_city"):
            address_parts.append(update_data["address_city"])
        if update_data.get("address_country"):
            address_parts.append(update_data["address_country"])
        
        if address_parts:
            update_data["address"] = ", ".join(address_parts)
            print(f"[BUILD] Erstelle vollständige Adresse für Update: {update_data['address']}")
    
    # Automatische Geocodierung wenn Adresse geändert wurde
    if update_data.get("address") and not update_data.get("address_latitude"):
        print(f"🌍 Geocodiere neue Adresse: {update_data['address']}")
        geocode_result = await geocode_address(update_data["address"])
        
        if geocode_result:
            update_data.update({
                "address_latitude": geocode_result["latitude"],
                "address_longitude": geocode_result["longitude"],
                "address_geocoded": True,
                "address_geocoding_date": datetime.utcnow()
            })
            print(f"[SUCCESS] Geocodierung erfolgreich: {geocode_result['latitude']}, {geocode_result['longitude']}")
    
    if update_data:
        await db.execute(
            update(Project)
            .where(Project.id == project_id)
            .values(**update_data, updated_at=datetime.utcnow())
        )
        await db.commit()
        await db.refresh(project)
    
    return project


async def delete_project(db: AsyncSession, project_id: int) -> bool:
    project = await get_project_by_id(db, project_id)
    if not project:
        return False
    
    await db.delete(project)
    await db.commit()
    return True


async def get_public_projects(db: AsyncSession, project_type: Optional[ProjectType] = None, region: Optional[str] = None) -> List[Project]:
    query = select(Project).where(
        Project.is_public == True,
        Project.allow_quotes == True,
        Project.status.in_([ProjectStatus.PLANNING, ProjectStatus.PREPARATION])
    )
    
    if project_type:
        query = query.where(Project.project_type == project_type)
    
    if region:
        query = query.where(Project.address.ilike(f"%{region}%"))
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_project_progress(db: AsyncSession, project_id: int) -> bool:
    """Aktualisiert den Projektfortschritt basierend auf abgeschlossenen Tasks und Milestones"""
    from ..models import Task, Milestone
    
    # Berechne Fortschritt basierend auf Tasks
    task_result = await db.execute(
        select(func.avg(Task.progress_percentage))
        .where(Task.project_id == project_id)
    )
    task_progress = task_result.scalar() or 0
    
    # Berechne Fortschritt basierend auf Milestones
    milestone_result = await db.execute(
        select(func.avg(Milestone.progress_percentage))
        .where(Milestone.project_id == project_id)
    )
    milestone_progress = milestone_result.scalar() or 0
    
    # Kombiniere beide Fortschritte (gewichtet)
    overall_progress = (task_progress * 0.6) + (milestone_progress * 0.4)
    
    await db.execute(
        update(Project)
        .where(Project.id == project_id)
        .values(progress_percentage=overall_progress, updated_at=datetime.utcnow())
    )
    await db.commit()
    return True


async def get_project_dashboard_data(db: AsyncSession, project_id: int) -> dict:
    """Holt alle Daten für das Projekt-Dashboard"""
    from ..models import Task, Milestone, Document, Quote
    
    project = await get_project_by_id(db, project_id)
    if not project:
        return {}
    
    # Task-Statistiken
    task_stats = await db.execute(
        select(
            func.count(Task.id).label('total'),
            func.count(Task.id).filter(Task.status == 'completed').label('completed')
        ).where(Task.project_id == project_id)
    )
    task_data = task_stats.first()
    
    # Milestone-Statistiken
    milestone_stats = await db.execute(
        select(
            func.count(Milestone.id).label('total'),
            func.count(Milestone.id).filter(Milestone.status == 'completed').label('completed')
        ).where(Milestone.project_id == project_id)
    )
    milestone_data = milestone_stats.first()
    
    # Dokumente und Angebote zählen
    document_count = await db.execute(
        select(func.count(Document.id)).where(Document.project_id == project_id)
    )
    quote_count = await db.execute(
        select(func.count(Quote.id)).where(Quote.project_id == project_id)
    )
    
    return {
        "project": project,
        "task_count": task_data.total if task_data else 0,
        "completed_tasks": task_data.completed if task_data else 0,
        "milestone_count": milestone_data.total if milestone_data else 0,
        "completed_milestones": milestone_data.completed if milestone_data else 0,
        "document_count": document_count.scalar() or 0,
        "quote_count": quote_count.scalar() or 0,
        "recent_activities": []  # TODO: Implementiere Aktivitätsverfolgung
    }


async def search_projects(db: AsyncSession, search_term: str, user_id: Optional[int] = None) -> List[Project]:
    query = select(Project)
    
    if user_id:
        query = query.where(Project.owner_id == user_id)
    
    # Suche in Name und Beschreibung
    search_filter = (
        Project.name.ilike(f"%{search_term}%") |
        Project.description.ilike(f"%{search_term}%") |
        Project.address.ilike(f"%{search_term}%")
    )
    
    query = query.where(search_filter)
    result = await db.execute(query)
    return list(result.scalars().all())
