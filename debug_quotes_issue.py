#!/usr/bin/env python3
"""
Debug-Skript für das Quotes-Problem
"""

import sqlite3

def debug_quotes():
    """Debuggt das Quotes-Problem"""
    try:
        con = sqlite3.connect('buildwise.db')
        cur = con.cursor()
        
        print("🔍 Debug: Quotes für Projekt 4")
        
        # Prüfe alle Quotes für Projekt 4
        cur.execute("SELECT id, title, status FROM quotes WHERE project_id = 4")
        quotes = cur.fetchall()
        print(f"Quotes für Projekt 4: {quotes}")
        
        # Prüfe alle Quotes insgesamt
        cur.execute("SELECT id, title, status, project_id FROM quotes")
        all_quotes = cur.fetchall()
        print(f"Alle Quotes: {all_quotes}")
        
        # Prüfe alle CostPositions
        cur.execute("SELECT id, title, quote_id, project_id FROM cost_positions")
        cost_positions = cur.fetchall()
        print(f"Alle CostPositions: {cost_positions}")
        
        # Prüfe CostPositions für Projekt 4
        cur.execute("SELECT id, title, quote_id FROM cost_positions WHERE project_id = 4")
        cp_project_4 = cur.fetchall()
        print(f"CostPositions für Projekt 4: {cp_project_4}")
        
        con.close()
        
    except Exception as e:
        print(f"Fehler: {e}")

if __name__ == "__main__":
    debug_quotes() 