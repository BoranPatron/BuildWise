#!/usr/bin/env python3
"""
Skript zum Umziehen aller Milestones, Quotes und CostPositions von project_id=1 auf project_id=4.
"""

import sqlite3
import os

OLD_PROJECT_ID = 1
NEW_PROJECT_ID = 4

def fix_project_assignment():
    db_path = "buildwise.db"
    if not os.path.exists(db_path):
        print(f"❌ Datenbank {db_path} nicht gefunden!")
        return
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print(f"🔧 Ziehe alle Milestones, Quotes und CostPositions von Projekt {OLD_PROJECT_ID} auf {NEW_PROJECT_ID} um...")
    # Milestones
    cursor.execute("UPDATE milestones SET project_id = ? WHERE project_id = ?", (NEW_PROJECT_ID, OLD_PROJECT_ID))
    print(f"  • {cursor.rowcount} Milestones verschoben")
    # Quotes
    cursor.execute("UPDATE quotes SET project_id = ? WHERE project_id = ?", (NEW_PROJECT_ID, OLD_PROJECT_ID))
    print(f"  • {cursor.rowcount} Quotes verschoben")
    # CostPositions
    cursor.execute("UPDATE cost_positions SET project_id = ? WHERE project_id = ?", (NEW_PROJECT_ID, OLD_PROJECT_ID))
    print(f"  • {cursor.rowcount} Kostenpositionen verschoben")
    conn.commit()
    conn.close()
    print("\n🎉 Umzug abgeschlossen!")

if __name__ == "__main__":
    fix_project_assignment() 