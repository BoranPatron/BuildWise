#!/usr/bin/env python3
"""
Skript zur Korrektur der Milestone-Status-Werte in der Datenbank.
Setzt alle Status-Werte auf die Enum-Namen (PLANNED, IN_PROGRESS, ...).
"""

import sqlite3
import os

def fix_milestone_status_values():
    """Setzt alle Milestone-Status-Werte auf die Enum-Namen (großgeschrieben)"""
    
    db_path = "buildwise.db"
    if not os.path.exists(db_path):
        print(f"❌ Datenbank {db_path} nicht gefunden!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 Setze Milestone-Status-Werte auf Enum-Namen...")
    
    # Mapping von Wert zu Enum-Name
    value_to_enum = {
        'planned': 'PLANNED',
        'in_progress': 'IN_PROGRESS',
        'completed': 'COMPLETED',
        'delayed': 'DELAYED',
        'cancelled': 'CANCELLED',
        'PLANNING': 'PLANNED',
        'IN_PROGRESS': 'IN_PROGRESS',
        'COMPLETED': 'COMPLETED',
        'DELAYED': 'DELAYED',
        'CANCELLED': 'CANCELLED',
    }
    
    # Prüfe aktuelle Status-Werte
    cursor.execute("SELECT DISTINCT status FROM milestones")
    current_statuses = [row[0] for row in cursor.fetchall()]
    print(f"📋 Aktuelle Status-Werte: {current_statuses}")
    
    # Korrigiere alle Werte
    for old_value, enum_name in value_to_enum.items():
        if old_value != enum_name:
            cursor.execute(
                "UPDATE milestones SET status = ? WHERE status = ?",
                (enum_name, old_value)
            )
            if cursor.rowcount > 0:
                print(f"✅ {cursor.rowcount} Milestones von '{old_value}' zu '{enum_name}' korrigiert")
    
    conn.commit()
    
    # Prüfe finale Status-Werte
    cursor.execute("SELECT DISTINCT status FROM milestones")
    final_statuses = [row[0] for row in cursor.fetchall()]
    print(f"📋 Finale Status-Werte: {final_statuses}")
    
    valid_statuses = ['PLANNED', 'IN_PROGRESS', 'COMPLETED', 'DELAYED', 'CANCELLED']
    invalid_statuses = [status for status in final_statuses if status not in valid_statuses]
    if invalid_statuses:
        print(f"❌ Ungültige Status-Werte gefunden: {invalid_statuses}")
        print(f"✅ Gültige Status-Werte: {valid_statuses}")
    else:
        print("✅ Alle Milestone-Status-Werte sind korrekt!")
    
    conn.close()

if __name__ == "__main__":
    print("🚀 Starte Milestone-Status-Korrektur...")
    fix_milestone_status_values()
    print("✅ Milestone-Status-Korrektur abgeschlossen!") 