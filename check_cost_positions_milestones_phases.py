#!/usr/bin/env python3
"""
Überprüfung der Bauphasen-Verteilung zwischen Kostenpositionen und Gewerken
"""

import sqlite3
from datetime import datetime

def check_construction_phases():
    """Überprüft die Bauphasen-Verteilung"""
    
    print("🔍 Überprüfung der Bauphasen-Verteilung")
    print("=" * 60)
    
    # SQLite-Verbindung
    conn = sqlite3.connect("buildwise.db")
    cursor = conn.cursor()
    
    try:
        # 1. Zeige alle Gewerke mit ihren Bauphasen
        print("\n📋 Gewerke (Milestones) und ihre Bauphasen:")
        cursor.execute("""
            SELECT id, title, project_id, construction_phase 
            FROM milestones 
            ORDER BY id
        """)
        milestones = cursor.fetchall()
        
        for milestone in milestones:
            milestone_id, title, project_id, construction_phase = milestone
            print(f"  • Gewerk {milestone_id}: '{title}' (Projekt: {project_id}, Bauphase: {construction_phase or 'Nicht gesetzt'})")
        
        # 2. Zeige alle Kostenpositionen mit ihren Bauphasen
        print("\n📋 Kostenpositionen und ihre Bauphasen:")
        cursor.execute("""
            SELECT id, title, project_id, milestone_id, construction_phase 
            FROM cost_positions 
            ORDER BY id
        """)
        cost_positions = cursor.fetchall()
        
        for cost_position in cost_positions:
            cp_id, title, project_id, milestone_id, construction_phase = cost_position
            print(f"  • Kostenposition {cp_id}: '{title}' (Projekt: {project_id}, Gewerk: {milestone_id}, Bauphase: {construction_phase or 'Nicht gesetzt'})")
        
        # 3. Zeige Kostenpositionen mit Gewerk-Verknüpfung
        print("\n🔗 Kostenpositionen mit Gewerk-Verknüpfung:")
        cursor.execute("""
            SELECT cp.id, cp.title, cp.project_id, cp.milestone_id, cp.construction_phase,
                   m.title as milestone_title, m.construction_phase as milestone_phase
            FROM cost_positions cp
            LEFT JOIN milestones m ON cp.milestone_id = m.id
            WHERE cp.milestone_id IS NOT NULL
            ORDER BY cp.id
        """)
        linked_cost_positions = cursor.fetchall()
        
        for cp in linked_cost_positions:
            cp_id, cp_title, project_id, milestone_id, cp_phase, milestone_title, milestone_phase = cp
            print(f"  • Kostenposition {cp_id}: '{cp_title}'")
            print(f"    - Projekt: {project_id}")
            print(f"    - Gewerk: {milestone_id} ('{milestone_title}')")
            print(f"    - Kostenposition Bauphase: {cp_phase or 'Nicht gesetzt'}")
            print(f"    - Gewerk Bauphase: {milestone_phase or 'Nicht gesetzt'}")
            print()
        
        # 4. Zeige Kostenpositionen ohne Gewerk-Verknüpfung
        print("\n📋 Kostenpositionen ohne Gewerk-Verknüpfung:")
        cursor.execute("""
            SELECT id, title, project_id, construction_phase
            FROM cost_positions 
            WHERE milestone_id IS NULL
            ORDER BY id
        """)
        unlinked_cost_positions = cursor.fetchall()
        
        for cp in unlinked_cost_positions:
            cp_id, title, project_id, construction_phase = cp
            print(f"  • Kostenposition {cp_id}: '{title}' (Projekt: {project_id}, Bauphase: {construction_phase or 'Nicht gesetzt'})")
        
        # 5. Statistiken
        print("\n📊 Statistiken:")
        
        # Gewerke mit Bauphase
        cursor.execute("""
            SELECT COUNT(*) FROM milestones WHERE construction_phase IS NOT NULL AND construction_phase != ''
        """)
        milestones_with_phase = cursor.fetchone()[0]
        
        # Gewerke ohne Bauphase
        cursor.execute("""
            SELECT COUNT(*) FROM milestones WHERE construction_phase IS NULL OR construction_phase = ''
        """)
        milestones_without_phase = cursor.fetchone()[0]
        
        # Kostenpositionen mit Bauphase
        cursor.execute("""
            SELECT COUNT(*) FROM cost_positions WHERE construction_phase IS NOT NULL AND construction_phase != ''
        """)
        cost_positions_with_phase = cursor.fetchone()[0]
        
        # Kostenpositionen ohne Bauphase
        cursor.execute("""
            SELECT COUNT(*) FROM cost_positions WHERE construction_phase IS NULL OR construction_phase = ''
        """)
        cost_positions_without_phase = cursor.fetchone()[0]
        
        # Kostenpositionen mit Gewerk-Verknüpfung
        cursor.execute("""
            SELECT COUNT(*) FROM cost_positions WHERE milestone_id IS NOT NULL
        """)
        cost_positions_with_milestone = cursor.fetchone()[0]
        
        print(f"  • Gewerke mit Bauphase: {milestones_with_phase}")
        print(f"  • Gewerke ohne Bauphase: {milestones_without_phase}")
        print(f"  • Kostenpositionen mit Bauphase: {cost_positions_with_phase}")
        print(f"  • Kostenpositionen ohne Bauphase: {cost_positions_without_phase}")
        print(f"  • Kostenpositionen mit Gewerk-Verknüpfung: {cost_positions_with_milestone}")
        
        # 6. Problem-Analyse
        print("\n🔍 Problem-Analyse:")
        
        # Kostenpositionen mit Gewerk-Verknüpfung aber ohne Bauphase
        cursor.execute("""
            SELECT cp.id, cp.title, cp.milestone_id, m.title as milestone_title, m.construction_phase
            FROM cost_positions cp
            LEFT JOIN milestones m ON cp.milestone_id = m.id
            WHERE cp.milestone_id IS NOT NULL 
            AND (cp.construction_phase IS NULL OR cp.construction_phase = '')
            AND (m.construction_phase IS NOT NULL AND m.construction_phase != '')
        """)
        missing_inheritance = cursor.fetchall()
        
        if missing_inheritance:
            print("  ⚠️ Kostenpositionen, die die Bauphase vom Gewerk erben sollten:")
            for cp in missing_inheritance:
                cp_id, cp_title, milestone_id, milestone_title, milestone_phase = cp
                print(f"    • Kostenposition {cp_id}: '{cp_title}'")
                print(f"      - Gewerk: {milestone_id} ('{milestone_title}')")
                print(f"      - Gewerk Bauphase: {milestone_phase}")
                print(f"      - Sollte erben: {milestone_phase}")
                print()
        else:
            print("  ✅ Alle Kostenpositionen haben korrekte Bauphasen-Vererbung")
        
    except Exception as e:
        print(f"❌ Fehler bei der Überprüfung: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    check_construction_phases() 