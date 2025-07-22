#!/usr/bin/env python3
"""
Debug-Skript für MilestoneSummary Schema-Problem
"""

import asyncio
import sqlite3
from datetime import datetime
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Import der Modelle
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.milestone import Milestone
from app.schemas.milestone import MilestoneSummary

async def debug_milestone_schema():
    """Debuggt das MilestoneSummary Schema"""
    
    # SQLite-Verbindung
    engine = create_engine("sqlite:///buildwise.db")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as db:
        try:
            print("🔧 Debug: Lade Milestones aus der Datenbank...")
            
            # Lade alle Milestones
            result = db.execute(select(Milestone))
            milestones = result.scalars().all()
            
            print(f"📊 {len(milestones)} Milestones gefunden")
            
            for i, milestone in enumerate(milestones):
                print(f"\n🔍 Milestone {i+1}:")
                print(f"  • ID: {milestone.id}")
                print(f"  • Title: {milestone.title}")
                print(f"  • Status: {milestone.status}")
                print(f"  • Priority: {milestone.priority}")
                print(f"  • Project ID: {milestone.project_id}")
                print(f"  • Construction Phase: {milestone.construction_phase}")
                print(f"  • Created At: {milestone.created_at}")
                print(f"  • Updated At: {milestone.updated_at}")
                
                # Teste Schema-Konvertierung
                try:
                    print("  🔧 Teste MilestoneSummary Schema...")
                    summary = MilestoneSummary.from_orm(milestone)
                    print(f"  ✅ Schema-Konvertierung erfolgreich")
                    print(f"  📋 Summary: {summary.dict()}")
                except Exception as e:
                    print(f"  ❌ Schema-Konvertierung fehlgeschlagen: {e}")
                    import traceback
                    traceback.print_exc()
                
                # Nur die ersten 3 Milestones testen
                if i >= 2:
                    break
            
        except Exception as e:
            print(f"❌ Fehler beim Debug: {e}")
            import traceback
            traceback.print_exc()


def test_milestone_model():
    """Testet das Milestone-Model direkt"""
    print("\n🧪 Teste Milestone-Model...")
    
    # SQLite-Verbindung
    conn = sqlite3.connect("buildwise.db")
    cursor = conn.cursor()
    
    try:
        # Prüfe Milestones-Tabelle
        cursor.execute("PRAGMA table_info(milestones)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Milestones-Tabelle Spalten: {columns}")
        
        # Prüfe ob construction_phase existiert
        if 'construction_phase' in columns:
            print("✅ construction_phase Spalte existiert")
        else:
            print("❌ construction_phase Spalte fehlt!")
        
        # Lade einige Milestones
        cursor.execute("SELECT id, title, status, priority, project_id, construction_phase FROM milestones LIMIT 3")
        rows = cursor.fetchall()
        
        print(f"\n📊 {len(rows)} Milestones aus Datenbank:")
        for row in rows:
            milestone_id, title, status, priority, project_id, construction_phase = row
            print(f"  • ID {milestone_id}: '{title}' (Status: {status}, Priority: {priority}, Project: {project_id}, Phase: {construction_phase})")
            
    except Exception as e:
        print(f"❌ Fehler beim Datenbank-Test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


async def main():
    """Hauptfunktion"""
    print("🔧 Debug MilestoneSummary Schema")
    print("=" * 50)
    
    # Teste Datenbank
    test_milestone_model()
    
    # Teste Schema
    await debug_milestone_schema()


if __name__ == "__main__":
    asyncio.run(main()) 