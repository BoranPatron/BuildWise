#!/usr/bin/env python3
"""
Listet alle angenommenen Angebote und die zugehörigen Kostenpositionen für alle Projekte auf.
"""

import sqlite3


def debug_accepted_quotes_and_cost_positions():
    print("🔍 Debug: Angenommene Angebote und Kostenpositionen pro Projekt")
    print("=" * 60)
    try:
        conn = sqlite3.connect('buildwise.db')
        cursor = conn.cursor()

        # Alle Projekte auflisten
        cursor.execute("SELECT id, name FROM projects")
        projects = cursor.fetchall()
        print(f"Gefundene Projekte: {len(projects)}\n")
        for project in projects:
            print(f"Projekt {project[0]}: {project[1]}")
            # Angenommene Angebote für dieses Projekt
            cursor.execute("""
                SELECT id, title, status, total_amount, currency FROM quotes WHERE project_id = ? AND status = 'accepted'
            """, (project[0],))
            quotes = cursor.fetchall()
            print(f"  Angenommene Angebote: {len(quotes)}")
            for quote in quotes:
                print(f"    - Angebot ID: {quote[0]}, Titel: {quote[1]}, Betrag: {quote[3]} {quote[4]}")
                # Kostenpositionen zu diesem Angebot
                cursor.execute("""
                    SELECT id, title, amount, currency, status FROM cost_positions WHERE quote_id = ?
                """, (quote[0],))
                cps = cursor.fetchall()
                if cps:
                    for cp in cps:
                        print(f"      → Kostenposition ID: {cp[0]}, Titel: {cp[1]}, Betrag: {cp[2]} {cp[3]}, Status: {cp[4]}")
                else:
                    print("      → Keine Kostenposition vorhanden!")
            print()
        conn.close()
        print("✅ Fertig.")
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    debug_accepted_quotes_and_cost_positions() 