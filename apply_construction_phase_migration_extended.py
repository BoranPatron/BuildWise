#!/usr/bin/env python3
"""
Erweiterte Migration für construction_phase in cost_positions und milestones Tabellen
Fügt das construction_phase Feld hinzu und aktualisiert bestehende Einträge
"""

import asyncio
import sqlite3
import os
from datetime import datetime

async def apply_construction_phase_migration_extended():
    """Führt die Migration für construction_phase in cost_positions und milestones aus"""
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print("❌ Datenbank buildwise.db nicht gefunden!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔧 Starte erweiterte Migration für construction_phase...")
        
        # 1. COST_POSITIONS TABELLE
        print("\n📊 COST_POSITIONS Tabelle:")
        print("-" * 40)
        
        # Prüfe ob die Spalte bereits existiert
        cursor.execute("PRAGMA table_info(cost_positions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'construction_phase' in columns:
            print("✅ Spalte construction_phase existiert bereits")
        else:
            print("➕ Füge construction_phase Spalte hinzu...")
            cursor.execute("""
                ALTER TABLE cost_positions 
                ADD COLUMN construction_phase TEXT
            """)
            print("✅ Spalte construction_phase hinzugefügt")
        
        # Erstelle Index für bessere Performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_cost_positions_construction_phase 
            ON cost_positions (construction_phase)
        """)
        print("✅ Index für construction_phase erstellt")
        
        # Aktualisiere bestehende cost_positions
        cursor.execute("""
            SELECT COUNT(*) FROM cost_positions 
            WHERE construction_phase IS NULL
        """)
        count_to_update = cursor.fetchone()[0]
        
        if count_to_update > 0:
            print(f"🔄 {count_to_update} cost_positions müssen aktualisiert werden")
            
            cursor.execute("""
                UPDATE cost_positions 
                SET construction_phase = (
                    SELECT construction_phase 
                    FROM projects 
                    WHERE projects.id = cost_positions.project_id
                )
                WHERE construction_phase IS NULL
            """)
            
            cursor.execute("""
                SELECT COUNT(*) FROM cost_positions 
                WHERE construction_phase IS NOT NULL
            """)
            updated_count = cursor.fetchone()[0]
            print(f"✅ {updated_count} cost_positions mit construction_phase aktualisiert")
        else:
            print("ℹ️ Keine cost_positions zum Aktualisieren gefunden")
        
        # 2. MILESTONES TABELLE
        print("\n📊 MILESTONES Tabelle:")
        print("-" * 40)
        
        # Prüfe ob die Spalte bereits existiert
        cursor.execute("PRAGMA table_info(milestones)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'construction_phase' in columns:
            print("✅ Spalte construction_phase existiert bereits")
        else:
            print("➕ Füge construction_phase Spalte hinzu...")
            cursor.execute("""
                ALTER TABLE milestones 
                ADD COLUMN construction_phase TEXT
            """)
            print("✅ Spalte construction_phase hinzugefügt")
        
        # Erstelle Index für bessere Performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_milestones_construction_phase 
            ON milestones (construction_phase)
        """)
        print("✅ Index für construction_phase erstellt")
        
        # Aktualisiere bestehende milestones
        cursor.execute("""
            SELECT COUNT(*) FROM milestones 
            WHERE construction_phase IS NULL
        """)
        count_to_update = cursor.fetchone()[0]
        
        if count_to_update > 0:
            print(f"🔄 {count_to_update} milestones müssen aktualisiert werden")
            
            cursor.execute("""
                UPDATE milestones 
                SET construction_phase = (
                    SELECT construction_phase 
                    FROM projects 
                    WHERE projects.id = milestones.project_id
                )
                WHERE construction_phase IS NULL
            """)
            
            cursor.execute("""
                SELECT COUNT(*) FROM milestones 
                WHERE construction_phase IS NOT NULL
            """)
            updated_count = cursor.fetchone()[0]
            print(f"✅ {updated_count} milestones mit construction_phase aktualisiert")
        else:
            print("ℹ️ Keine milestones zum Aktualisieren gefunden")
        
        # 3. GESAMTSTATISTIKEN
        print("\n📊 Gesamtstatistiken:")
        print("-" * 40)
        
        # Cost Positions Statistiken
        cursor.execute("SELECT COUNT(*) FROM cost_positions")
        total_cost_positions = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM cost_positions 
            WHERE construction_phase IS NOT NULL AND construction_phase != ''
        """)
        cost_positions_with_phase = cursor.fetchone()[0]
        
        # Milestones Statistiken
        cursor.execute("SELECT COUNT(*) FROM milestones")
        total_milestones = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM milestones 
            WHERE construction_phase IS NOT NULL AND construction_phase != ''
        """)
        milestones_with_phase = cursor.fetchone()[0]
        
        print(f"📋 Cost Positions:")
        print(f"  - Gesamt: {total_cost_positions}")
        print(f"  - Mit Bauphase: {cost_positions_with_phase}")
        print(f"  - Ohne Bauphase: {total_cost_positions - cost_positions_with_phase}")
        
        print(f"📋 Milestones:")
        print(f"  - Gesamt: {total_milestones}")
        print(f"  - Mit Bauphase: {milestones_with_phase}")
        print(f"  - Ohne Bauphase: {total_milestones - milestones_with_phase}")
        
        # 4. BAUPHASEN-VERTEILUNG
        print("\n🏗️ Bauphasen-Verteilung:")
        print("-" * 40)
        
        # Cost Positions nach Bauphasen
        cursor.execute("""
            SELECT construction_phase, COUNT(*) 
            FROM cost_positions 
            WHERE construction_phase IS NOT NULL AND construction_phase != ''
            GROUP BY construction_phase
        """)
        cost_positions_phases = cursor.fetchall()
        
        if cost_positions_phases:
            print(f"📊 Cost Positions nach Bauphasen:")
            for phase, count in cost_positions_phases:
                print(f"  • {phase}: {count} Kostenpositionen")
        
        # Milestones nach Bauphasen
        cursor.execute("""
            SELECT construction_phase, COUNT(*) 
            FROM milestones 
            WHERE construction_phase IS NOT NULL AND construction_phase != ''
            GROUP BY construction_phase
        """)
        milestones_phases = cursor.fetchall()
        
        if milestones_phases:
            print(f"📊 Milestones nach Bauphasen:")
            for phase, count in milestones_phases:
                print(f"  • {phase}: {count} Gewerke")
        
        # 5. TESTE DIE FUNKTIONALITÄT
        print("\n🧪 Teste Funktionalität...")
        
        # Teste cost_positions mit construction_phase
        cursor.execute("""
            SELECT id, title, construction_phase, project_id 
            FROM cost_positions 
            WHERE construction_phase IS NOT NULL AND construction_phase != ''
            LIMIT 2
        """)
        cost_positions_test = cursor.fetchall()
        
        if cost_positions_test:
            print("✅ Cost Positions Test erfolgreich:")
            for cost_pos_id, title, phase, project_id in cost_positions_test:
                print(f"  • ID {cost_pos_id}: '{title}' (Phase: {phase}, Projekt: {project_id})")
        
        # Teste milestones mit construction_phase
        cursor.execute("""
            SELECT id, title, construction_phase, project_id 
            FROM milestones 
            WHERE construction_phase IS NOT NULL AND construction_phase != ''
            LIMIT 2
        """)
        milestones_test = cursor.fetchall()
        
        if milestones_test:
            print("✅ Milestones Test erfolgreich:")
            for milestone_id, title, phase, project_id in milestones_test:
                print(f"  • ID {milestone_id}: '{title}' (Phase: {phase}, Projekt: {project_id})")
        
        conn.commit()
        print("\n✅ Erweiterte Migration erfolgreich abgeschlossen!")
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei der Migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def test_milestone_creation():
    """Testet die Erstellung eines neuen Gewerks mit construction_phase"""
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print("❌ Datenbank buildwise.db nicht gefunden!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n🧪 Teste Gewerk-Erstellung...")
        
        # Finde ein Projekt mit construction_phase
        cursor.execute("""
            SELECT id, name, construction_phase 
            FROM projects 
            WHERE construction_phase IS NOT NULL AND construction_phase != ''
            LIMIT 1
        """)
        project = cursor.fetchone()
        
        if not project:
            print("❌ Kein Projekt mit construction_phase gefunden!")
            return False
        
        project_id, project_name, construction_phase = project
        print(f"📋 Teste mit Projekt: {project_name} (Phase: {construction_phase})")
        
        # Erstelle ein Test-Gewerk
        test_title = f"Test Gewerk - {datetime.now().strftime('%H:%M:%S')}"
        test_planned_date = datetime.now().date()
        
        cursor.execute("""
            INSERT INTO milestones (
                project_id, created_by, title, description, status, priority,
                planned_date, construction_phase, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id, 1, test_title, "Test Beschreibung", "planned", "medium",
            test_planned_date, construction_phase, datetime.now(), datetime.now()
        ))
        
        # Hole das erstellte Gewerk
        cursor.execute("""
            SELECT id, title, construction_phase 
            FROM milestones 
            WHERE title = ?
        """, (test_title,))
        
        created_milestone = cursor.fetchone()
        
        if created_milestone:
            milestone_id, title, phase = created_milestone
            print(f"✅ Test-Gewerk erstellt:")
            print(f"  • ID: {milestone_id}")
            print(f"  • Titel: {title}")
            print(f"  • Bauphase: {phase}")
            
            # Lösche das Test-Gewerk
            cursor.execute("DELETE FROM milestones WHERE id = ?", (milestone_id,))
            print(f"🗑️ Test-Gewerk gelöscht")
        else:
            print("❌ Test-Gewerk konnte nicht erstellt werden")
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Test: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


async def main():
    """Hauptfunktion"""
    print("🏗️ Erweiterte Construction Phase Migration")
    print("=" * 60)
    
    # Führe Migration aus
    if await apply_construction_phase_migration_extended():
        print("\n✅ Migration erfolgreich!")
        
        # Teste Funktionalität
        if test_milestone_creation():
            print("\n✅ Funktionalität getestet!")
        else:
            print("\n❌ Funktionalität-Test fehlgeschlagen!")
    else:
        print("\n❌ Migration fehlgeschlagen!")


if __name__ == "__main__":
    asyncio.run(main()) 