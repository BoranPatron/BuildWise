from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import uuid

from ..models import Milestone, Project
from ..schemas.milestone import MilestoneCreate, MilestoneUpdate


def aggregate_category_specific_fields(
    base_description: str,
    category: str,
    category_specific_fields: Dict[str, Any],
    technical_specifications: str = "",
    quality_requirements: str = "",
    safety_requirements: str = "",
    environmental_requirements: str = "",
    notes: str = ""
) -> str:
    """
    Aggregiert alle kategorie-spezifischen Felder und zusätzliche Informationen
    in einen strukturierten Text für das description Feld.
    """
    sections = []
    
    # Basis-Beschreibung hinzufügen
    if base_description.strip():
        sections.append(f"📋 **Beschreibung:**\n{base_description.strip()}")
    
    # Kategorie-spezifische Felder hinzufügen
    if category_specific_fields:
        sections.append(f"\n🔧 **Kategorie-spezifische Details ({category.upper()}):**")
        
        for field_id, value in category_specific_fields.items():
            if value is not None and value != "":
                # Feld-ID in lesbaren Text umwandeln
                field_label = field_id.replace('_', ' ').title()
                if isinstance(value, bool):
                    field_value = "Ja" if value else "Nein"
                else:
                    field_value = str(value)
                sections.append(f"• {field_label}: {field_value}")
    
    # Technische Spezifikationen
    if technical_specifications.strip():
        sections.append(f"\n⚙️ **Technische Spezifikationen:**\n{technical_specifications.strip()}")
    
    # Qualitätsanforderungen
    if quality_requirements.strip():
        sections.append(f"\n🎯 **Qualitätsanforderungen:**\n{quality_requirements.strip()}")
    
    # Sicherheitsanforderungen
    if safety_requirements.strip():
        sections.append(f"\n🛡️ **Sicherheitsanforderungen:**\n{safety_requirements.strip()}")
    
    # Umweltanforderungen
    if environmental_requirements.strip():
        sections.append(f"\n🌱 **Umweltanforderungen:**\n{environmental_requirements.strip()}")
    
    # Notizen
    if notes.strip():
        sections.append(f"\n📝 **Notizen:**\n{notes.strip()}")
    
    return "\n".join(sections)


async def create_milestone(db: AsyncSession, milestone_in: MilestoneCreate, created_by: int) -> Milestone:
    """Erstellt ein neues Gewerk mit automatischer Bauphasen-Zuordnung und aggregierten Beschreibungen"""
    from ..models import Project
    
    # Hole das Projekt, um die aktuelle Bauphase zu ermitteln
    project_result = await db.execute(
        select(Project).where(Project.id == milestone_in.project_id)
    )
    project = project_result.scalar_one_or_none()
    
    # Aggregiere alle Informationen in das description Feld
    aggregated_description = aggregate_category_specific_fields(
        base_description=milestone_in.description or "",
        category=milestone_in.category or "",
        category_specific_fields=getattr(milestone_in, 'category_specific_fields', {}),
        technical_specifications=getattr(milestone_in, 'technical_specifications', ""),
        quality_requirements=getattr(milestone_in, 'quality_requirements', ""),
        safety_requirements=getattr(milestone_in, 'safety_requirements', ""),
        environmental_requirements=getattr(milestone_in, 'environmental_requirements', ""),
        notes=milestone_in.notes or ""
    )
    
    # Erstelle das Gewerk
    milestone_data = {
        'project_id': milestone_in.project_id,
        'created_by': created_by,
        'title': milestone_in.title,
        'description': aggregated_description,  # Verwende die aggregierte Beschreibung
        'status': milestone_in.status,
        'priority': milestone_in.priority,
        'category': milestone_in.category,
        'planned_date': milestone_in.planned_date,
        'start_date': milestone_in.start_date,
        'end_date': milestone_in.end_date,
        'budget': milestone_in.budget,
        'actual_costs': milestone_in.actual_costs,
        'contractor': milestone_in.contractor,
        'is_critical': milestone_in.is_critical,
        'notify_on_completion': milestone_in.notify_on_completion,
        'notes': milestone_in.notes,
        # Besichtigungssystem
        'requires_inspection': milestone_in.requires_inspection
    }
    
    # Setze automatisch die aktuelle Bauphase des Projekts
    if project and project.construction_phase:
        milestone_data['construction_phase'] = project.construction_phase
        print(f"🏗️ Gewerk erstellt mit Bauphase: {project.construction_phase}")
    else:
        print(f"⚠️ Projekt hat keine Bauphase gesetzt")
    
    milestone = Milestone(**milestone_data)
    db.add(milestone)
    await db.commit()
    await db.refresh(milestone)
    return milestone


async def get_milestone_by_id(db: AsyncSession, milestone_id: int) -> Milestone | None:
    result = await db.execute(select(Milestone).where(Milestone.id == milestone_id))
    return result.scalars().first()


async def get_milestones_for_project(db: AsyncSession, project_id: int) -> List[Milestone]:
    result = await db.execute(
        select(Milestone)
        .where(Milestone.project_id == project_id)
        .order_by(Milestone.planned_date)
    )
    return list(result.scalars().all())


async def get_all_milestones_for_user(db: AsyncSession, user_id: int) -> List[Milestone]:
    """Holt alle Gewerke für alle Projekte des Benutzers"""
    # Hole alle Projekte des Benutzers
    projects_result = await db.execute(
        select(Project.id).where(Project.owner_id == user_id)
    )
    project_ids = [row[0] for row in projects_result.fetchall()]
    
    if not project_ids:
        return []
    
    # Hole alle Gewerke für diese Projekte
    result = await db.execute(
        select(Milestone)
        .where(Milestone.project_id.in_(project_ids))
        .order_by(Milestone.planned_date)
    )
    return list(result.scalars().all())


async def update_milestone(db: AsyncSession, milestone_id: int, milestone_update: MilestoneUpdate) -> Milestone | None:
    milestone = await get_milestone_by_id(db, milestone_id)
    if not milestone:
        return None
    
    update_data = milestone_update.dict(exclude_unset=True)
    if update_data:
        # Wenn Meilenstein abgeschlossen wird, setze completed_at
        new_status = update_data.get('status')
        if new_status == "completed" and milestone.status != "completed":
            update_data['completed_at'] = datetime.utcnow()
            update_data['progress_percentage'] = 100
            update_data['actual_date'] = datetime.utcnow().date()
        
        await db.execute(
            update(Milestone)
            .where(Milestone.id == milestone_id)
            .values(**update_data, updated_at=datetime.utcnow())
        )
        await db.commit()
        await db.refresh(milestone)
    
    return milestone


async def delete_milestone(db: AsyncSession, milestone_id: int) -> bool:
    milestone = await get_milestone_by_id(db, milestone_id)
    if not milestone:
        return False
    
    await db.delete(milestone)
    await db.commit()
    return True


async def get_milestone_statistics(db: AsyncSession, project_id: int) -> dict:
    """Holt Statistiken für Meilensteine eines Projekts"""
    result = await db.execute(
        select(
            func.count(Milestone.id).label('total'),
            func.count(Milestone.id).filter(Milestone.status == "planned").label('planned'),
            func.count(Milestone.id).filter(Milestone.status == "in_progress").label('in_progress'),
            func.count(Milestone.id).filter(Milestone.status == "completed").label('completed'),
            func.count(Milestone.id).filter(Milestone.status == "delayed").label('delayed'),
            func.avg(Milestone.progress_percentage).label('avg_progress')
        ).where(Milestone.project_id == project_id)
    )
    
    stats = result.first()
    
    return {
        "total": int(stats.total) if stats and stats.total is not None else 0,
        "planned": int(stats.planned) if stats and stats.planned is not None else 0,
        "in_progress": int(stats.in_progress) if stats and stats.in_progress is not None else 0,
        "completed": int(stats.completed) if stats and stats.completed is not None else 0,
        "delayed": int(stats.delayed) if stats and stats.delayed is not None else 0,
        "avg_progress": round(float(stats.avg_progress), 1) if stats and stats.avg_progress is not None else 0.0
    }


async def get_upcoming_milestones(db: AsyncSession, project_id: Optional[int] = None, days: int = 30) -> List[Milestone]:
    """Holt anstehende Meilensteine in den nächsten X Tagen"""
    from datetime import date, timedelta
    
    start_date = date.today()
    end_date = start_date + timedelta(days=days)
    
    query = select(Milestone).where(
        Milestone.planned_date >= start_date,
        Milestone.planned_date <= end_date,
        Milestone.status.in_(["planned", "in_progress"])
    )
    
    if project_id:
        query = query.where(Milestone.project_id == project_id)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_overdue_milestones(db: AsyncSession, project_id: Optional[int] = None) -> List[Milestone]:
    """Holt überfällige Meilensteine"""
    from datetime import date
    
    query = select(Milestone).where(
        Milestone.planned_date < date.today(),
        Milestone.status.in_(["planned", "in_progress"])
    )
    
    if project_id:
        query = query.where(Milestone.project_id == project_id)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def search_milestones(db: AsyncSession, search_term: str, project_id: Optional[int] = None) -> List[Milestone]:
    query = select(Milestone)
    
    if project_id:
        query = query.where(Milestone.project_id == project_id)
    
    # Suche in Titel und Beschreibung
    search_filter = (
        Milestone.title.ilike(f"%{search_term}%") |
        Milestone.description.ilike(f"%{search_term}%")
    )
    
    query = query.where(search_filter)
    result = await db.execute(query)
    return list(result.scalars().all()) 


async def get_all_active_milestones(db: AsyncSession) -> list:
    from ..models import Project
    from ..models.quote import Quote, QuoteStatus
    import logging
    session_id = str(uuid.uuid4())
    logging.warning(f"[SERVICE] get_all_active_milestones: Session {session_id} gestartet")
    
    # Debug: Prüfe alle Projekte
    projects_result = await db.execute(select(Project))
    all_projects = list(projects_result.scalars().all())
    logging.warning(f"[SERVICE] Session {session_id}: Alle Projekte: {len(all_projects)}")
    for p in all_projects:
        logging.warning(f"[SERVICE] Session {session_id}: Projekt: id={p.id}, name={p.name}, is_public={p.is_public}, allow_quotes={p.allow_quotes}")
    
    # Debug: Prüfe alle Milestones
    milestones_result = await db.execute(select(Milestone))
    all_milestones = list(milestones_result.scalars().all())
    logging.warning(f"[SERVICE] Session {session_id}: Alle Milestones: {len(all_milestones)}")
    for m in all_milestones:
        logging.warning(f"[SERVICE] Session {session_id}: Milestone: id={m.id}, status={m.status}, project_id={m.project_id}")
    
    # Alle aktiven Gewerke zurückgeben (unabhängig von Projekt-Öffentlichkeit)
    result = await db.execute(
        select(Milestone)
        .where(
            Milestone.status.in_(["planned", "in_progress"])
        )
        .order_by(Milestone.planned_date)
    )
    milestones = list(result.scalars().all())
    
    # Lade Quote-Statistiken für jedes Milestone
    milestones_with_stats = []
    for milestone in milestones:
        # Lade alle Quotes für dieses Milestone
        quote_result = await db.execute(
            select(Quote).where(Quote.milestone_id == milestone.id)
        )
        quotes = list(quote_result.scalars().all())
        
        # Berechne Quote-Statistiken
        total_quotes = len(quotes)
        accepted_quotes = len([q for q in quotes if q.status == QuoteStatus.ACCEPTED])
        pending_quotes = len([q for q in quotes if q.status in [QuoteStatus.SUBMITTED, QuoteStatus.UNDER_REVIEW]])
        rejected_quotes = len([q for q in quotes if q.status == QuoteStatus.REJECTED])
        
        # Erstelle ein Dictionary mit Milestone-Daten und Quote-Stats
        milestone_dict = {
            "id": milestone.id,
            "title": milestone.title,
            "description": milestone.description,
            "category": milestone.category,
            "status": milestone.status,
            "priority": milestone.priority,
            "budget": milestone.budget,
            "planned_date": milestone.planned_date.isoformat() if milestone.planned_date else None,
            "start_date": milestone.start_date.isoformat() if milestone.start_date else None,
            "end_date": milestone.end_date.isoformat() if milestone.end_date else None,
            "progress_percentage": milestone.progress_percentage,
            "contractor": milestone.contractor,
            "requires_inspection": getattr(milestone, 'requires_inspection', False),
            "project_id": milestone.project_id,
            "created_at": milestone.created_at.isoformat() if milestone.created_at else None,
            "updated_at": milestone.updated_at.isoformat() if milestone.updated_at else None,
            # Quote-Statistiken hinzufügen
            "quote_stats": {
                "total_quotes": total_quotes,
                "accepted_quotes": accepted_quotes,
                "pending_quotes": pending_quotes,
                "rejected_quotes": rejected_quotes,
                "has_accepted_quote": accepted_quotes > 0,
                "has_pending_quotes": pending_quotes > 0,
                "has_rejected_quotes": rejected_quotes > 0
            }
        }
        milestones_with_stats.append(milestone_dict)
    
    logging.warning(f"[SERVICE] Session {session_id}: get_all_active_milestones: {len(milestones_with_stats)} gefunden mit Quote-Stats.")
    for m in milestones_with_stats:
        logging.warning(f"[SERVICE] Session {session_id}: Milestone: id={m['id']}, title={m['title']}, quotes={m['quote_stats']['total_quotes']}")
    
    return milestones_with_stats


async def get_milestones_by_construction_phase(db: AsyncSession, project_id: int, construction_phase: str) -> List[Milestone]:
    """Holt Gewerke nach Bauphase"""
    result = await db.execute(
        select(Milestone)
        .where(
            Milestone.project_id == project_id,
            Milestone.construction_phase == construction_phase
        )
        .order_by(Milestone.planned_date)
    )
    return list(result.scalars().all())


async def get_milestone_statistics_by_phase(db: AsyncSession, project_id: int) -> dict:
    """Holt Statistiken für Gewerke nach Bauphasen"""
    # Gesamtanzahl pro Bauphase
    phase_distribution_result = await db.execute(
        select(
            Milestone.construction_phase,
            func.count(Milestone.id).label('count'),
            func.sum(Milestone.budget).label('total_budget'),
            func.sum(Milestone.actual_costs).label('total_costs'),
            func.avg(Milestone.progress_percentage).label('avg_progress')
        )
        .where(Milestone.project_id == project_id)
        .group_by(Milestone.construction_phase)
    )
    
    phase_distribution = {}
    for row in phase_distribution_result.all():
        phase = row.construction_phase or 'Keine Phase'
        phase_distribution[phase] = {
            'count': row.count,
            'total_budget': float(row.total_budget or 0),
            'total_costs': float(row.total_costs or 0),
            'avg_progress': round(float(row.avg_progress or 0), 1),
            'budget_variance': float((row.total_budget or 0) - (row.total_costs or 0))
        }
    
    # Gesamtstatistiken
    total_stats_result = await db.execute(
        select(
            func.count(Milestone.id).label('total_count'),
            func.sum(Milestone.budget).label('total_budget'),
            func.sum(Milestone.actual_costs).label('total_costs'),
            func.avg(Milestone.progress_percentage).label('avg_progress')
        )
        .where(Milestone.project_id == project_id)
    )
    
    total_stats = total_stats_result.scalar_one()
    
    return {
        "phase_distribution": phase_distribution,
        "total_count": total_stats.total_count,
        "total_budget": float(total_stats.total_budget or 0),
        "total_costs": float(total_stats.total_costs or 0),
        "avg_progress": round(float(total_stats.avg_progress or 0), 1),
        "total_budget_variance": float((total_stats.total_budget or 0) - (total_stats.total_costs or 0))
    } 