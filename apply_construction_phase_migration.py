#!/usr/bin/env python3
"""
Migration-Skript für construction_phase in cost_positions Tabelle
Fügt das construction_phase Feld hinzu und aktualisiert bestehende Einträge
"""

import asyncio
import sqlite3
import os
from datetime import datetime

async def apply_construction_phase_migration():
    """Führt die Migration für construction_phase in cost_positions aus"""
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print("❌ Datenbank buildwise.db nicht gefunden!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔧 Starte Migration für construction_phase in cost_positions...")
        
        # 1. Prüfe ob die Spalte bereits existiert
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
        
        # 2. Erstelle Index für bessere Performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_cost_positions_construction_phase 
            ON cost_positions (construction_phase)
        """)
        print("✅ Index für construction_phase erstellt")
        
        # 3. Aktualisiere bestehende cost_positions mit construction_phase aus Projekten
        print("🔄 Aktualisiere bestehende cost_positions...")
        
        # Zähle zu aktualisierende Einträge
        cursor.execute("""
            SELECT COUNT(*) FROM cost_positions 
            WHERE construction_phase IS NULL
        """)
        count_to_update = cursor.fetchone()[0]
        
        if count_to_update > 0:
            print(f"📊 {count_to_update} cost_positions müssen aktualisiert werden")
            
            # Aktualisiere construction_phase aus Projekten
            cursor.execute("""
                UPDATE cost_positions 
                SET construction_phase = (
                    SELECT construction_phase 
                    FROM projects 
                    WHERE projects.id = cost_positions.project_id
                )
                WHERE construction_phase IS NULL
            """)
            
            # Prüfe wie viele aktualisiert wurden
            cursor.execute("""
                SELECT COUNT(*) FROM cost_positions 
                WHERE construction_phase IS NOT NULL
            """)
            updated_count = cursor.fetchone()[0]
            
            print(f"✅ {updated_count} cost_positions mit construction_phase aktualisiert")
        else:
            print("ℹ️ Keine cost_positions zum Aktualisieren gefunden")
        
        # 4. Zeige Statistiken
        print("\n📊 Migration-Statistiken:")
        
        # Gesamtanzahl cost_positions
        cursor.execute("SELECT COUNT(*) FROM cost_positions")
        total_count = cursor.fetchone()[0]
        print(f"  - Gesamt cost_positions: {total_count}")
        
        # Mit construction_phase
        cursor.execute("""
            SELECT COUNT(*) FROM cost_positions 
            WHERE construction_phase IS NOT NULL AND construction_phase != ''
        """)
        with_phase_count = cursor.fetchone()[0]
        print(f"  - Mit construction_phase: {with_phase_count}")
        
        # Ohne construction_phase
        cursor.execute("""
            SELECT COUNT(*) FROM cost_positions 
            WHERE construction_phase IS NULL OR construction_phase = ''
        """)
        without_phase_count = cursor.fetchone()[0]
        print(f"  - Ohne construction_phase: {without_phase_count}")
        
        # Verteilung nach Bauphasen
        cursor.execute("""
            SELECT construction_phase, COUNT(*) 
            FROM cost_positions 
            WHERE construction_phase IS NOT NULL AND construction_phase != ''
            GROUP BY construction_phase
        """)
        phase_distribution = cursor.fetchall()
        
        if phase_distribution:
            print(f"  - Bauphasen-Verteilung:")
            for phase, count in phase_distribution:
                print(f"    • {phase}: {count} Kostenpositionen")
        
        # 5. Teste die Funktionalität
        print("\n🧪 Teste Funktionalität...")
        
        # Teste ob eine cost_position mit construction_phase existiert
        cursor.execute("""
            SELECT id, title, construction_phase, project_id 
            FROM cost_positions 
            WHERE construction_phase IS NOT NULL AND construction_phase != ''
            LIMIT 3
        """)
        test_results = cursor.fetchall()
        
        if test_results:
            print("✅ Test erfolgreich - Beispiele:")
            for cost_pos_id, title, phase, project_id in test_results:
                print(f"  • ID {cost_pos_id}: '{title}' (Phase: {phase}, Projekt: {project_id})")
        else:
            print("⚠️ Keine cost_positions mit construction_phase gefunden")
        
        conn.commit()
        print("\n✅ Migration erfolgreich abgeschlossen!")
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei der Migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def test_cost_position_creation():
    """Testet die Erstellung einer neuen Kostenposition mit construction_phase"""
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print("❌ Datenbank buildwise.db nicht gefunden!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n🧪 Teste Kostenposition-Erstellung...")
        
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
        
        # Erstelle eine Test-Kostenposition
        test_title = f"Test Kostenposition - {datetime.now().strftime('%H:%M:%S')}"
        test_amount = 1500.00
        
        cursor.execute("""
            INSERT INTO cost_positions (
                project_id, title, amount, currency, category, cost_type, status,
                construction_phase, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id, test_title, test_amount, "EUR", "other", "manual", "active",
            construction_phase, datetime.now(), datetime.now()
        ))
        
        # Hole die erstellte Kostenposition
        cursor.execute("""
            SELECT id, title, construction_phase 
            FROM cost_positions 
            WHERE title = ?
        """, (test_title,))
        
        created_cost_position = cursor.fetchone()
        
        if created_cost_position:
            cost_pos_id, title, phase = created_cost_position
            print(f"✅ Test-Kostenposition erstellt:")
            print(f"  • ID: {cost_pos_id}")
            print(f"  • Titel: {title}")
            print(f"  • Bauphase: {phase}")
            
            # Lösche die Test-Kostenposition
            cursor.execute("DELETE FROM cost_positions WHERE id = ?", (cost_pos_id,))
            print(f"🗑️ Test-Kostenposition gelöscht")
        else:
            print("❌ Test-Kostenposition konnte nicht erstellt werden")
        
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
    print("🏗️ Construction Phase Migration für Cost Positions")
    print("=" * 60)
    
    # Führe Migration aus
    if await apply_construction_phase_migration():
        print("\n✅ Migration erfolgreich!")
        
        # Teste Funktionalität
        if test_cost_position_creation():
            print("\n✅ Funktionalität getestet!")
        else:
            print("\n❌ Funktionalität-Test fehlgeschlagen!")
    else:
        print("\n❌ Migration fehlgeschlagen!")


if __name__ == "__main__":
    asyncio.run(main()) 