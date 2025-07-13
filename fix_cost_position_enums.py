#!/usr/bin/env python3
"""
Korrigiert ungültige Kategorien und Cost Types in der CostPosition-Tabelle auf gültige Enum-Werte
"""

import sqlite3
import os

def fix_cost_position_enums():
    print("🔧 Korrigiere ungültige Kategorien und Cost Types in CostPosition-Tabelle...")
    db_path = "buildwise.db"
    if not os.path.exists(db_path):
        print(f"❌ Datenbank {db_path} nicht gefunden")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        # Korrigiere Kategorie 'electrical' -> 'ELECTRICAL'
        cursor.execute("SELECT id, category FROM cost_positions WHERE category = 'electrical'")
        rows = cursor.fetchall()
        print(f"📊 Gefundene Einträge mit 'electrical': {len(rows)}")
        for row in rows:
            print(f"  - ID: {row[0]}, Kategorie: {row[1]}")
        cursor.execute("UPDATE cost_positions SET category = 'ELECTRICAL' WHERE category = 'electrical'")
        print(f"✅ {cursor.rowcount} Kategorie-Einträge korrigiert")

        # Korrigiere cost_type 'service' -> 'MANUAL'
        cursor.execute("SELECT id, cost_type FROM cost_positions WHERE cost_type = 'service'")
        rows = cursor.fetchall()
        print(f"📊 Gefundene Einträge mit cost_type 'service': {len(rows)}")
        for row in rows:
            print(f"  - ID: {row[0]}, cost_type: {row[1]}")
        cursor.execute("UPDATE cost_positions SET cost_type = 'MANUAL' WHERE cost_type = 'service'")
        print(f"✅ {cursor.rowcount} cost_type-Einträge korrigiert")

        conn.commit()
    except Exception as e:
        print(f"❌ Fehler: {e}")
    finally:
        conn.close()
        print("🔒 Verbindung geschlossen")

if __name__ == "__main__":
    fix_cost_position_enums()
    print("✅ Korrektur abgeschlossen") 