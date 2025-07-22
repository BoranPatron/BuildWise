#!/usr/bin/env python3
"""
Skript zur Nachholung der Bauphasen-Vererbung für bestehende Kostenpositionen
"""

import sqlite3
from datetime import datetime

def fix_cost_positions_construction_phase():
    """Holt die Bauphasen-Vererbung für bestehende Kostenpositionen nach"""
    
    print("🔧 Nachholung der Bauphasen-Vererbung für bestehende Kostenpositionen")
    print("=" * 70)
    
    # SQLite-Verbindung
    conn = sqlite3.connect("buildwise.db")
    cursor = conn.cursor()
    
    try:
        # 1. Zeige den aktuellen Zustand
        print("\n📋 Aktueller Zustand vor der Korrektur:")
        
        cursor.execute("""
            SELECT cp.id, cp.title, cp.milestone_id, cp.construction_phase,
                   m.title as milestone_title, m.construction_phase as milestone_phase
            FROM cost_positions cp
            LEFT JOIN milestones m ON cp.milestone_id = m.id
            WHERE cp.milestone_id IS NOT NULL
            ORDER BY cp.id
        """)
        current_state = cursor.fetchall()
        
        for cp in current_state:
            cp_id, cp_title, milestone_id, cp_phase, milestone_title, milestone_phase = cp
            print(f"  • Kostenposition {cp_id}: '{cp_title}'")
            print(f"    - Gewerk: {milestone_id} ('{milestone_title}')")
            print(f"    - Aktuelle Bauphase: {cp_phase or 'Nicht gesetzt'}")
            print(f"    - Gewerk Bauphase: {milestone_phase or 'Nicht gesetzt'}")
            print()
        
        # 2. Finde Kostenpositionen, die die Bauphase vom Gewerk erben sollten
        print("🔍 Finde Kostenpositionen für Bauphasen-Vererbung...")
        
        cursor.execute("""
            SELECT cp.id, cp.title, cp.milestone_id, cp.construction_phase,
                   m.title as milestone_title, m.construction_phase as milestone_phase
            FROM cost_positions cp
            LEFT JOIN milestones m ON cp.milestone_id = m.id
            WHERE cp.milestone_id IS NOT NULL 
            AND (cp.construction_phase IS NULL OR cp.construction_phase = '')
            AND (m.construction_phase IS NOT NULL AND m.construction_phase != '')
        """)
        to_fix = cursor.fetchall()
        
        if not to_fix:
            print("  ✅ Alle Kostenpositionen haben bereits korrekte Bauphasen-Vererbung")
            return
        
        print(f"  📋 {len(to_fix)} Kostenpositionen gefunden, die korrigiert werden müssen:")
        
        for cp in to_fix:
            cp_id, cp_title, milestone_id, cp_phase, milestone_title, milestone_phase = cp
            print(f"    • Kostenposition {cp_id}: '{cp_title}'")
            print(f"      - Gewerk: {milestone_id} ('{milestone_title}')")
            print(f"      - Gewerk Bauphase: {milestone_phase}")
            print(f"      - Soll erben: {milestone_phase}")
            print()
        
        # 3. Führe die Korrektur durch
        print("🔧 Führe Bauphasen-Vererbung durch...")
        
        updated_count = 0
        for cp in to_fix:
            cp_id, cp_title, milestone_id, cp_phase, milestone_title, milestone_phase = cp
            
            # Update die Kostenposition mit der Bauphase vom Gewerk
            cursor.execute("""
                UPDATE cost_positions 
                SET construction_phase = ? 
                WHERE id = ?
            """, (milestone_phase, cp_id))
            
            print(f"  ✅ Kostenposition {cp_id}: '{cp_title}'")
            print(f"     - Gewerk: {milestone_id} ('{milestone_title}')")
            print(f"     - Bauphase übernommen: {milestone_phase}")
            print()
            
            updated_count += 1
        
        # 4. Commit die Änderungen
        conn.commit()
        print(f"✅ {updated_count} Kostenpositionen erfolgreich aktualisiert")
        
        # 5. Zeige den neuen Zustand
        print("\n📋 Neuer Zustand nach der Korrektur:")
        
        cursor.execute("""
            SELECT cp.id, cp.title, cp.milestone_id, cp.construction_phase,
                   m.title as milestone_title, m.construction_phase as milestone_phase
            FROM cost_positions cp
            LEFT JOIN milestones m ON cp.milestone_id = m.id
            WHERE cp.milestone_id IS NOT NULL
            ORDER BY cp.id
        """)
        new_state = cursor.fetchall()
        
        for cp in new_state:
            cp_id, cp_title, milestone_id, cp_phase, milestone_title, milestone_phase = cp
            print(f"  • Kostenposition {cp_id}: '{cp_title}'")
            print(f"    - Gewerk: {milestone_id} ('{milestone_title}')")
            print(f"    - Neue Bauphase: {cp_phase or 'Nicht gesetzt'}")
            print(f"    - Gewerk Bauphase: {milestone_phase or 'Nicht gesetzt'}")
            print()
        
        # 6. Statistiken
        print("📊 Aktualisierte Statistiken:")
        
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
        
        print(f"  • Kostenpositionen mit Bauphase: {cost_positions_with_phase}")
        print(f"  • Kostenpositionen ohne Bauphase: {cost_positions_without_phase}")
        print(f"  • Kostenpositionen mit Gewerk-Verknüpfung: {cost_positions_with_milestone}")
        
        # 7. Verteilung nach Bauphasen
        print("\n📋 Verteilung nach Bauphasen:")
        cursor.execute("""
            SELECT construction_phase, COUNT(*) 
            FROM cost_positions 
            WHERE construction_phase IS NOT NULL AND construction_phase != ''
            GROUP BY construction_phase
        """)
        phase_distribution = cursor.fetchall()
        
        for phase, count in phase_distribution:
            print(f"  • {phase}: {count} Kostenpositionen")
        
        print(f"\n✅ Bauphasen-Vererbung erfolgreich nachgeholt!")
        print(f"   - {updated_count} Kostenpositionen aktualisiert")
        print(f"   - {cost_positions_with_phase} Kostenpositionen haben jetzt eine Bauphase")
        
    except Exception as e:
        print(f"❌ Fehler bei der Korrektur: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    fix_cost_positions_construction_phase() 