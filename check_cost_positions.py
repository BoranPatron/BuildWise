#!/usr/bin/env python3
"""
Skript zur Überprüfung der Kostenpositionen für ein Projekt und ein Quote.
"""

import sqlite3
import os

PROJECT_ID = 4  # Jetzt für Hausbau Boran


def check_cost_positions():
    db_path = "buildwise.db"
    if not os.path.exists(db_path):
        print(f"❌ Datenbank {db_path} nicht gefunden!")
        return
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print(f"🔍 Kostenpositionen für Projekt {PROJECT_ID}:")
    cursor.execute("SELECT id, title, amount, cost_type, quote_id, project_id, milestone_id FROM cost_positions WHERE project_id = ?", (PROJECT_ID,))
    rows = cursor.fetchall()
    if not rows:
        print("⚠️  Keine Kostenpositionen für dieses Projekt gefunden!")
    else:
        for row in rows:
            print(f"  • ID: {row[0]}, Titel: {row[1]}, Betrag: {row[2]}, Typ: {row[3]}, Quote: {row[4]}, Projekt: {row[5]}, Milestone: {row[6]}")
    conn.close()
    print("\n🎉 Überprüfung abgeschlossen!")

if __name__ == "__main__":
    check_cost_positions() 