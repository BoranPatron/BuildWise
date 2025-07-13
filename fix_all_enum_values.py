#!/usr/bin/env python3
"""
Fix All Enum Values Script
Korrigiert alle ungültigen Enum-Werte in der Datenbank
"""

import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_database_url

async def fix_all_enum_values():
    """Korrigiert alle ungültigen Enum-Werte in der Datenbank"""
    
    print("🔧 Starte umfassende Enum-Wert-Korrektur...")
    
    # Erstelle Datenbankverbindung
    database_url = get_database_url()
    engine = create_async_engine(database_url, echo=False)
    
    async_session = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    
    try:
        async with async_session() as session:
            
            # 1. Korrigiere Projekt-Status
            print("\n📋 1. Korrigiere Projekt-Status...")
            
            # Finde alle ungültigen Projekt-Status
            result = await session.execute(
                text("SELECT id, name, status FROM projects WHERE status NOT IN ('PLANNING', 'PREPARATION', 'EXECUTION', 'COMPLETION', 'COMPLETED', 'ON_HOLD', 'CANCELLED')")
            )
            invalid_status_projects = result.fetchall()
            
            if invalid_status_projects:
                print(f"⚠️  Gefunden: {len(invalid_status_projects)} Projekte mit ungültigem Status")
                for project in invalid_status_projects:
                    print(f"   - Projekt {project.id}: '{project.name}' (Status: {project.status})")
                
                # Korrigiere auf 'PLANNING'
                await session.execute(
                    text("UPDATE projects SET status = 'PLANNING' WHERE status NOT IN ('PLANNING', 'PREPARATION', 'EXECUTION', 'COMPLETION', 'COMPLETED', 'ON_HOLD', 'CANCELLED')")
                )
                print("✅ Projekt-Status korrigiert")
            else:
                print("✅ Alle Projekt-Status sind korrekt")
            
            # 2. Korrigiere Projekt-Typen
            print("\n📋 2. Korrigiere Projekt-Typen...")
            
            # Finde alle ungültigen Projekt-Typen
            result = await session.execute(
                text("SELECT id, name, project_type FROM projects WHERE project_type NOT IN ('new_build', 'renovation', 'extension', 'refurbishment')")
            )
            invalid_type_projects = result.fetchall()
            
            if invalid_type_projects:
                print(f"⚠️  Gefunden: {len(invalid_type_projects)} Projekte mit ungültigem Typ")
                for project in invalid_type_projects:
                    print(f"   - Projekt {project.id}: '{project.name}' (Typ: {project.project_type})")
                
                # Korrigiere auf 'new_build'
                await session.execute(
                    text("UPDATE projects SET project_type = 'new_build' WHERE project_type NOT IN ('new_build', 'renovation', 'extension', 'refurbishment')")
                )
                print("✅ Projekt-Typen korrigiert")
            else:
                print("✅ Alle Projekt-Typen sind korrekt")
            
            # 3. Korrigiere Milestone-Status
            print("\n📋 3. Korrigiere Milestone-Status...")
            
            # Finde alle ungültigen Milestone-Status
            result = await session.execute(
                text("SELECT id, title, status FROM milestones WHERE status NOT IN ('planned', 'in_progress', 'completed', 'delayed', 'cancelled')")
            )
            invalid_milestone_status = result.fetchall()
            
            if invalid_milestone_status:
                print(f"⚠️  Gefunden: {len(invalid_milestone_status)} Milestones mit ungültigem Status")
                for milestone in invalid_milestone_status:
                    print(f"   - Milestone {milestone.id}: '{milestone.title}' (Status: {milestone.status})")
                
                # Korrigiere auf 'planned'
                await session.execute(
                    text("UPDATE milestones SET status = 'planned' WHERE status NOT IN ('planned', 'in_progress', 'completed', 'delayed', 'cancelled')")
                )
                print("✅ Milestone-Status korrigiert")
            else:
                print("✅ Alle Milestone-Status sind korrekt")
            
            # 4. Korrigiere Task-Status
            print("\n📋 4. Korrigiere Task-Status...")
            
            # Finde alle ungültigen Task-Status
            result = await session.execute(
                text("SELECT id, title, status FROM tasks WHERE status NOT IN ('todo', 'in_progress', 'review', 'completed', 'cancelled')")
            )
            invalid_task_status = result.fetchall()
            
            if invalid_task_status:
                print(f"⚠️  Gefunden: {len(invalid_task_status)} Tasks mit ungültigem Status")
                for task in invalid_task_status:
                    print(f"   - Task {task.id}: '{task.title}' (Status: {task.status})")
                
                # Korrigiere auf 'todo'
                await session.execute(
                    text("UPDATE tasks SET status = 'todo' WHERE status NOT IN ('todo', 'in_progress', 'review', 'completed', 'cancelled')")
                )
                print("✅ Task-Status korrigiert")
            else:
                print("✅ Alle Task-Status sind korrekt")
            
            # 5. Korrigiere Task-Prioritäten
            print("\n📋 5. Korrigiere Task-Prioritäten...")
            
            # Finde alle ungültigen Task-Prioritäten
            result = await session.execute(
                text("SELECT id, title, priority FROM tasks WHERE priority NOT IN ('low', 'medium', 'high', 'urgent')")
            )
            invalid_task_priority = result.fetchall()
            
            if invalid_task_priority:
                print(f"⚠️  Gefunden: {len(invalid_task_priority)} Tasks mit ungültiger Priorität")
                for task in invalid_task_priority:
                    print(f"   - Task {task.id}: '{task.title}' (Priorität: {task.priority})")
                
                # Korrigiere auf 'medium'
                await session.execute(
                    text("UPDATE tasks SET priority = 'medium' WHERE priority NOT IN ('low', 'medium', 'high', 'urgent')")
                )
                print("✅ Task-Prioritäten korrigiert")
            else:
                print("✅ Alle Task-Prioritäten sind korrekt")
            
            # 6. Korrigiere Quote-Status
            print("\n📋 6. Korrigiere Quote-Status...")
            
            # Finde alle ungültigen Quote-Status
            result = await session.execute(
                text("SELECT id, title, status FROM quotes WHERE status NOT IN ('draft', 'submitted', 'under_review', 'accepted', 'rejected', 'expired')")
            )
            invalid_quote_status = result.fetchall()
            
            if invalid_quote_status:
                print(f"⚠️  Gefunden: {len(invalid_quote_status)} Quotes mit ungültigem Status")
                for quote in invalid_quote_status:
                    print(f"   - Quote {quote.id}: '{quote.title}' (Status: {quote.status})")
                
                # Korrigiere auf 'draft'
                await session.execute(
                    text("UPDATE quotes SET status = 'draft' WHERE status NOT IN ('draft', 'submitted', 'under_review', 'accepted', 'rejected', 'expired')")
                )
                print("✅ Quote-Status korrigiert")
            else:
                print("✅ Alle Quote-Status sind korrekt")
            
            # 7. Korrigiere User-Typen
            print("\n📋 7. Korrigiere User-Typen...")
            
            # Finde alle ungültigen User-Typen
            result = await session.execute(
                text("SELECT id, email, user_type FROM users WHERE user_type NOT IN ('PROFESSIONAL', 'SERVICE_PROVIDER', 'ADMIN')")
            )
            invalid_user_types = result.fetchall()
            
            if invalid_user_types:
                print(f"⚠️  Gefunden: {len(invalid_user_types)} User mit ungültigem Typ")
                for user in invalid_user_types:
                    print(f"   - User {user.id}: '{user.email}' (Typ: {user.user_type})")
                
                # Korrigiere auf 'PROFESSIONAL'
                await session.execute(
                    text("UPDATE users SET user_type = 'PROFESSIONAL' WHERE user_type NOT IN ('PROFESSIONAL', 'SERVICE_PROVIDER', 'ADMIN')")
                )
                print("✅ User-Typen korrigiert")
            else:
                print("✅ Alle User-Typen sind korrekt")
            
            await session.commit()
            print("\n✅ Alle Enum-Werte erfolgreich korrigiert!")
                
    except Exception as e:
        print(f"❌ Fehler beim Korrigieren der Enum-Werte: {e}")
        raise
    finally:
        await engine.dispose()

async def check_all_enum_values():
    """Prüft alle Enum-Werte in der Datenbank"""
    
    print("🔍 Prüfe alle Enum-Werte...")
    
    database_url = get_database_url()
    engine = create_async_engine(database_url, echo=False)
    
    async_session = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    
    try:
        async with async_session() as session:
            
            # Prüfe Projekte
            print("\n📊 Projekte:")
            result = await session.execute(text("SELECT status, COUNT(*) as count FROM projects GROUP BY status"))
            project_statuses = result.fetchall()
            for status, count in project_statuses:
                print(f"   - Status '{status}': {count} Projekte")
            
            result = await session.execute(text("SELECT project_type, COUNT(*) as count FROM projects GROUP BY project_type"))
            project_types = result.fetchall()
            for project_type, count in project_types:
                print(f"   - Typ '{project_type}': {count} Projekte")
            
            # Prüfe Milestones
            print("\n📊 Milestones:")
            result = await session.execute(text("SELECT status, COUNT(*) as count FROM milestones GROUP BY status"))
            milestone_statuses = result.fetchall()
            for status, count in milestone_statuses:
                print(f"   - Status '{status}': {count} Milestones")
            
            # Prüfe Tasks
            print("\n📊 Tasks:")
            result = await session.execute(text("SELECT status, COUNT(*) as count FROM tasks GROUP BY status"))
            task_statuses = result.fetchall()
            for status, count in task_statuses:
                print(f"   - Status '{status}': {count} Tasks")
            
            result = await session.execute(text("SELECT priority, COUNT(*) as count FROM tasks GROUP BY priority"))
            task_priorities = result.fetchall()
            for priority, count in task_priorities:
                print(f"   - Priorität '{priority}': {count} Tasks")
            
            # Prüfe Quotes
            print("\n📊 Quotes:")
            result = await session.execute(text("SELECT status, COUNT(*) as count FROM quotes GROUP BY status"))
            quote_statuses = result.fetchall()
            for status, count in quote_statuses:
                print(f"   - Status '{status}': {count} Quotes")
            
            # Prüfe Users
            print("\n📊 Users:")
            result = await session.execute(text("SELECT user_type, COUNT(*) as count FROM users GROUP BY user_type"))
            user_types = result.fetchall()
            for user_type, count in user_types:
                print(f"   - Typ '{user_type}': {count} Users")
                
    except Exception as e:
        print(f"❌ Fehler beim Prüfen der Enum-Werte: {e}")
        raise
    finally:
        await engine.dispose()

async def main():
    """Hauptfunktion"""
    print("🚀 BuildWise - Umfassende Enum-Wert-Korrektur")
    print("=" * 60)
    
    try:
        # Prüfe aktuelle Enum-Werte
        await check_all_enum_values()
        print("\n" + "=" * 60)
        
        # Korrigiere ungültige Enum-Werte
        await fix_all_enum_values()
        print("\n" + "=" * 60)
        
        # Prüfe Enum-Werte nach Korrektur
        await check_all_enum_values()
        
        print("\n✅ Umfassende Enum-Wert-Korrektur erfolgreich abgeschlossen!")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 