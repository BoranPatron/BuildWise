#!/usr/bin/env python3
"""
Skript zur Überprüfung aller Quotes und ihrer Status.
"""

import sqlite3
import os

def check_quotes_status():
    """Überprüft alle Quotes und ihre Status"""
    
    db_path = "buildwise.db"
    if not os.path.exists(db_path):
        print(f"❌ Datenbank {db_path} nicht gefunden!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Überprüfe alle Quotes...")
    
    # Hole alle Quotes mit Status
    cursor.execute("SELECT id, title, status, project_id, milestone_id, total_amount FROM quotes")
    quotes = cursor.fetchall()
    
    print(f"📊 Gesamte Quotes: {len(quotes)}")
    
    if quotes:
        print("📋 Alle Quotes:")
        for quote in quotes:
            quote_id, title, status, project_id, milestone_id, total_amount = quote
            print(f"  • ID: {quote_id}, Titel: {title}, Status: {status}, Projekt: {project_id}, Milestone: {milestone_id}, Betrag: {total_amount}")
    else:
        print("⚠️  Keine Quotes in der Datenbank")
    
    # Status-Verteilung
    cursor.execute("SELECT status, COUNT(*) FROM quotes GROUP BY status")
    status_distribution = cursor.fetchall()
    
    print(f"\n📊 Status-Verteilung:")
    for status, count in status_distribution:
        print(f"  • {status}: {count}")
    
    conn.close()
    print("\n🎉 Überprüfung abgeschlossen!")

if __name__ == "__main__":
    check_quotes_status() 