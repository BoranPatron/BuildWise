"""
Service für automatische Task-Erstellung bei Mängeln
Behandelt die Erstellung von Tasks für Dienstleister bei dokumentierten Mängeln
und Wiedervorlage-Tasks für Bauträger bei Abnahme unter Vorbehalt
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timedelta

from ..models import Task, TaskStatus, TaskPriority, AcceptanceDefect, Acceptance, User, Milestone
from ..schemas.task import TaskCreate


async def create_defect_task_for_service_provider(
    db: AsyncSession,
    defect: AcceptanceDefect,
    acceptance: Acceptance,
    created_by_user_id: int
) -> Task:
    """
    Erstellt automatisch eine Task für den Dienstleister zur Behebung eines Mangels
    
    Args:
        db: Database Session
        defect: Der dokumentierte Mangel
        acceptance: Die zugehörige Abnahme
        created_by_user_id: User-ID des Bauträgers der die Abnahme durchführt
    
    Returns:
        Task: Die erstellte Task für den Dienstleister
    """
    
    # Bestimme Priorität basierend auf Schweregrad
    priority_mapping = {
        'MINOR': TaskPriority.MEDIUM,
        'MAJOR': TaskPriority.HIGH,
        'CRITICAL': TaskPriority.URGENT
    }
    priority = priority_mapping.get(defect.severity.value, TaskPriority.MEDIUM)
    
    # Bestimme Frist basierend auf Schweregrad
    deadline_days = {
        'MINOR': 14,    # 2 Wochen für geringfügige Mängel
        'MAJOR': 7,     # 1 Woche für erhebliche Mängel
        'CRITICAL': 3   # 3 Tage für kritische Mängel
    }
    days = deadline_days.get(defect.severity.value, 14)
    due_date = (datetime.now() + timedelta(days=days)).date()
    
    # Hole Milestone (Gewerk) Details
    milestone = await db.execute(select(Milestone).where(Milestone.id == acceptance.milestone_id))
    milestone = milestone.scalars().first()
    
    # Bestimme zugewiesenen Dienstleister
    assigned_to = acceptance.service_provider_id or acceptance.contractor_id
    
    # Erstelle Task-Titel und Beschreibung
    task_title = f"Mangel beheben: {defect.title}"
    if milestone:
        task_title = f"[{milestone.title}] {task_title}"
    
    # Erstelle detaillierte Beschreibung mit allen Informationen
    photo_count = len(defect.photos or [])
    photo_info = ""
    if photo_count > 0:
        photo_info = f"\n📸 **Anhänge:**\n"
        for i, photo_url in enumerate(defect.photos or [], 1):
            photo_info += f"- Foto {i}: {photo_url}\n"
    
    task_description = f"""🔧 MANGELBEHEBUNG ERFORDERLICH

📋 **Mangel-Details:**
- **Schweregrad:** {defect.severity.value} ({'Geringfügig' if defect.severity.value == 'MINOR' else 'Erheblich' if defect.severity.value == 'MAJOR' else 'Kritisch'})
- **Ort:** {defect.location or 'Nicht angegeben'}
- **Raum:** {defect.room or 'Nicht angegeben'}

📝 **Beschreibung:**
{defect.description}

📅 **Frist:** {due_date.strftime('%d.%m.%Y')} ({days} Tage)
{photo_info}
🏗️ **Gewerk:** {milestone.title if milestone else 'Unbekannt'}

⚠️ **Wichtig:** 
- Nach Behebung bitte Fotos der erledigten Arbeiten hochladen
- Task als "Erledigt" markieren wenn vollständig behoben
- Bei Fragen kontaktieren Sie den Bauträger über das Projekt

🔗 **Abnahme-ID:** {acceptance.id}
"""

    # Erstelle Task
    task = Task(
        project_id=acceptance.project_id,
        milestone_id=acceptance.milestone_id,
        assigned_to=assigned_to,
        created_by=created_by_user_id,
        title=task_title,
        description=task_description,
        status=TaskStatus.TODO,
        priority=priority,
        due_date=due_date,
        is_milestone=False
    )
    
    db.add(task)
    await db.flush()  # Flush um task.id zu bekommen, aber noch nicht committen
    
    # Verknüpfe Task mit Mangel
    defect.task_id = task.id
    defect.deadline = datetime.combine(due_date, datetime.min.time())
    
    # Ein einziger Commit für beide Änderungen
    await db.commit()
    await db.refresh(task)
    
    print(f"✅ Task für Mangel '{defect.title}' erstellt (ID: {task.id}) - Zugewiesen an User {assigned_to}")
    
    return task


async def create_review_task_for_bautraeger(
    db: AsyncSession,
    acceptance: Acceptance,
    created_by_user_id: int
) -> Task:
    """
    Erstellt eine Wiedervorlage-Task für den Bauträger bei Abnahme unter Vorbehalt
    
    Args:
        db: Database Session
        acceptance: Die Abnahme unter Vorbehalt
        created_by_user_id: User-ID des Bauträgers
    
    Returns:
        Task: Die erstellte Wiedervorlage-Task
    """
    
    # Hole Milestone (Gewerk) Details
    milestone = await db.execute(select(Milestone).where(Milestone.id == acceptance.milestone_id))
    milestone = milestone.scalars().first()
    
    # Hole Bauträger (Project Owner)
    # TODO: Hier sollte der tatsächliche Bauträger ermittelt werden
    # Für jetzt nehmen wir den User der die Abnahme erstellt hat
    bautraeger_id = created_by_user_id
    
    # Erstelle Task-Titel und Beschreibung
    task_title = f"Wiedervorlage: Abnahme unter Vorbehalt"
    if milestone:
        task_title = f"[{milestone.title}] {task_title}"
    
    defect_count = len(acceptance.defects) if acceptance.defects else 0
    
    task_description = f"""📋 WIEDERVORLAGE: ABNAHME UNTER VORBEHALT

🏗️ **Gewerk:** {milestone.title if milestone else 'Unbekannt'}
📅 **Ursprüngliche Abnahme:** {acceptance.created_at.strftime('%d.%m.%Y') if acceptance.created_at else 'Unbekannt'}
📅 **Wiedervorlage-Datum:** {acceptance.review_date.strftime('%d.%m.%Y') if acceptance.review_date else 'Nicht gesetzt'}

⚠️ **Dokumentierte Mängel:** {defect_count}

📝 **Notizen zur Wiedervorlage:**
{acceptance.review_notes or 'Keine Notizen'}

🔄 **Nächste Schritte:**
1. Prüfen Sie den Fortschritt der Mangelbehebung
2. Kontaktieren Sie den Dienstleister bei Verzögerungen
3. Planen Sie eine erneute Abnahme sobald alle Mängel behoben sind
4. Dokumentieren Sie den aktuellen Status

💡 **Tipp:** Überprüfen Sie die zugehörigen Mangel-Tasks um den aktuellen Bearbeitungsstand zu sehen.
"""

    # Erstelle Task - Review-Task soll in "Überprüfung" Spalte stehen
    task = Task(
        project_id=acceptance.project_id,
        milestone_id=acceptance.milestone_id,
        assigned_to=bautraeger_id,
        created_by=created_by_user_id,
        title=task_title,
        description=task_description,
        status=TaskStatus.REVIEW,  # Review-Task direkt in Überprüfung-Spalte
        priority=TaskPriority.MEDIUM,
        due_date=acceptance.review_date,
        is_milestone=False
    )
    
    db.add(task)
    await db.flush()  # Flush um task.id zu bekommen, aber noch nicht committen
    
    # Verknüpfe Task mit Acceptance
    acceptance.review_task_id = task.id
    
    # Ein einziger Commit für beide Änderungen
    await db.commit()
    await db.refresh(task)
    
    print(f"✅ Wiedervorlage-Task für Abnahme erstellt (ID: {task.id}) - Zugewiesen an Bauträger {bautraeger_id}")
    
    return task


async def process_acceptance_completion(
    db: AsyncSession,
    acceptance: Acceptance,
    created_by_user_id: int
) -> dict:
    """
    Verarbeitet eine abgeschlossene Abnahme und erstellt automatisch Tasks
    
    Args:
        db: Database Session
        acceptance: Die abgeschlossene Abnahme
        created_by_user_id: User-ID des Bauträgers
    
    Returns:
        dict: Zusammenfassung der erstellten Tasks
    """
    
    result = {
        'defect_tasks_created': 0,
        'review_task_created': False,
        'defect_tasks': [],
        'review_task': None
    }
    
    # 1. Erstelle Tasks für alle dokumentierten Mängel
    if acceptance.defects:
        for defect in acceptance.defects:
            if not defect.resolved and not defect.task_id:  # Nur für ungelöste Mängel ohne bestehende Task
                try:
                    task = await create_defect_task_for_service_provider(
                        db=db,
                        defect=defect,
                        acceptance=acceptance,
                        created_by_user_id=created_by_user_id
                    )
                    result['defect_tasks'].append(task)
                    result['defect_tasks_created'] += 1
                except Exception as e:
                    print(f"❌ Fehler beim Erstellen der Mangel-Task für '{defect.title}': {e}")
    
    # 2. Erstelle Wiedervorlage-Task wenn Abnahme unter Vorbehalt
    if not acceptance.accepted and acceptance.review_date and not acceptance.review_task_id:
        try:
            review_task = await create_review_task_for_bautraeger(
                db=db,
                acceptance=acceptance,
                created_by_user_id=created_by_user_id
            )
            result['review_task'] = review_task
            result['review_task_created'] = True
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der Wiedervorlage-Task: {e}")
    
    print(f"📊 Acceptance-Verarbeitung abgeschlossen: {result['defect_tasks_created']} Mangel-Tasks, {'1' if result['review_task_created'] else '0'} Wiedervorlage-Task")
    
    return result


async def mark_defect_as_resolved(
    db: AsyncSession,
    defect_id: int,
    resolved_by_user_id: int,
    resolution_notes: str = "",
    resolution_photos: List[str] = None
) -> bool:
    """
    Markiert einen Mangel als behoben und schließt die zugehörige Task ab
    
    Args:
        db: Database Session
        defect_id: ID des Mangels
        resolved_by_user_id: User-ID des Dienstleisters
        resolution_notes: Notizen zur Behebung
        resolution_photos: Fotos der Behebung
    
    Returns:
        bool: True wenn erfolgreich
    """
    
    # Hole Mangel
    result = await db.execute(select(AcceptanceDefect).where(AcceptanceDefect.id == defect_id))
    defect = result.scalars().first()
    
    if not defect:
        print(f"❌ Mangel mit ID {defect_id} nicht gefunden")
        return False
    
    # Markiere Mangel als behoben
    defect.resolved = True
    defect.resolved_at = datetime.now()
    defect.resolved_by = resolved_by_user_id
    defect.resolution_notes = resolution_notes
    if resolution_photos:
        defect.resolution_photos = resolution_photos
    
    # Schließe zugehörige Task ab
    if defect.task_id:
        task_result = await db.execute(select(Task).where(Task.id == defect.task_id))
        task = task_result.scalars().first()
        
        if task:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.progress_percentage = 100
            
            # Füge Auflösungsnotizen zur Task-Beschreibung hinzu
            if resolution_notes:
                task.description += f"\n\n✅ **BEHOBEN am {datetime.now().strftime('%d.%m.%Y %H:%M')}**\n{resolution_notes}"
            
            print(f"✅ Task {task.id} für Mangel '{defect.title}' als erledigt markiert")
    
    await db.commit()
    
    print(f"✅ Mangel '{defect.title}' als behoben markiert")
    return True