#!/usr/bin/env python3
"""
Behebt ungültige Enum-Werte direkt in der SQLite-Datenbank
"""

import sqlite3
import os


def fix_database_enums():
    """Behebt ungültige Enum-Werte direkt in der Datenbank"""
    print("🔧 Behebe ungültige Enum-Werte direkt in der Datenbank...")
    
    db_path = "buildwise.db"
    if not os.path.exists(db_path):
        print(f"❌ Datenbank {db_path} nicht gefunden")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Prüfe aktuelle Werte
        cursor.execute("SELECT id, category, cost_type, status FROM cost_positions")
        rows = cursor.fetchall()
        
        print(f"📊 Gefundene CostPositions: {len(rows)}")
        
        fixed_count = 0
        for row in rows:
            cost_position_id, category, cost_type, status = row
            needs_fix = False
            
            # Prüfe und korrigiere Kategorie
            if category not in ['ELECTRICAL', 'PLUMBING', 'HEATING', 'ROOFING', 'MASONRY', 'DRYWALL', 'PAINTING', 'FLOORING', 'LANDSCAPING', 'KITCHEN', 'BATHROOM', 'OTHER']:
                print(f"  ⚠️ CostPosition {cost_position_id}: Ungültige Kategorie '{category}' -> ELECTRICAL")
                category = 'ELECTRICAL'
                needs_fix = True
            
            # Prüfe und korrigiere Cost Type
            if cost_type not in ['LABOR', 'MATERIAL', 'EQUIPMENT', 'SERVICES', 'PERMITS', 'OTHER']:
                print(f"  ⚠️ CostPosition {cost_position_id}: Ungültiger Cost Type '{cost_type}' -> LABOR")
                cost_type = 'LABOR'
                needs_fix = True
            
            # Prüfe und korrigiere Status
            if status not in ['ACTIVE', 'COMPLETED', 'CANCELLED', 'ON_HOLD']:
                print(f"  ⚠️ CostPosition {cost_position_id}: Ungültiger Status '{status}' -> ACTIVE")
                status = 'ACTIVE'
                needs_fix = True
            
            if needs_fix:
                cursor.execute(
                    "UPDATE cost_positions SET category = ?, cost_type = ?, status = ? WHERE id = ?",
                    (category, cost_type, status, cost_position_id)
                )
                fixed_count += 1
        
        if fixed_count > 0:
            conn.commit()
            print(f"✅ {fixed_count} CostPositions erfolgreich korrigiert")
        else:
            print("✅ Keine Korrekturen nötig")
        
        # Prüfe ob jetzt alles funktioniert
        print("\n🔍 Teste erneut...")
        cursor.execute("SELECT COUNT(*) FROM cost_positions WHERE project_id = 4")
        count = cursor.fetchone()[0]
        print(f"✅ {count} CostPositions für Projekt 4 erfolgreich geladen")
        
        # Zeige Details
        cursor.execute("SELECT id, title, category, cost_type, status FROM cost_positions WHERE project_id = 4")
        rows = cursor.fetchall()
        for row in rows:
            cost_position_id, title, category, cost_type, status = row
            print(f"  - CostPosition {cost_position_id}: {title} ({category}/{cost_type}/{status})")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        conn.rollback()
    finally:
        conn.close()


def main():
    """Hauptfunktion"""
    print("🚀 Starte direkte Datenbank-Korrektur")
    fix_database_enums()
    print("✅ Datenbank-Korrektur abgeschlossen")


if __name__ == "__main__":
    main() 