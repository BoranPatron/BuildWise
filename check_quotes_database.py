#!/usr/bin/env python3
"""
Skript zur Überprüfung der Quotes-Datenbank und Debugging.
"""

import sqlite3
import os

def check_quotes_database():
    """Überprüft die Quotes-Datenbank und zeigt Probleme an"""
    
    db_path = "buildwise.db"
    if not os.path.exists(db_path):
        print(f"❌ Datenbank {db_path} nicht gefunden!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Überprüfe Quotes-Datenbank...")
    
    # 1. Prüfe ob quotes-Tabelle existiert
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quotes'")
    if not cursor.fetchone():
        print("❌ Quotes-Tabelle existiert nicht!")
        return
    
    print("✅ Quotes-Tabelle existiert")
    
    # 2. Prüfe Tabellenstruktur
    cursor.execute("PRAGMA table_info(quotes)")
    columns = cursor.fetchall()
    print(f"📋 Quotes-Tabelle hat {len(columns)} Spalten:")
    for col in columns:
        print(f"  • {col[1]} ({col[2]})")
    
    # 3. Zähle Quotes
    cursor.execute("SELECT COUNT(*) FROM quotes")
    quote_count = cursor.fetchone()[0]
    print(f"📊 Anzahl Quotes: {quote_count}")
    
    # 4. Zeige alle Quotes
    if quote_count > 0:
        cursor.execute("SELECT id, title, status, milestone_id, project_id FROM quotes")
        quotes = cursor.fetchall()
        print("📋 Alle Quotes:")
        for quote in quotes:
            print(f"  • ID: {quote[0]}, Titel: {quote[1]}, Status: {quote[2]}, Milestone: {quote[3]}, Projekt: {quote[4]}")
    else:
        print("⚠️  Keine Quotes in der Datenbank")
    
    # 5. Prüfe Milestones
    cursor.execute("SELECT COUNT(*) FROM milestones")
    milestone_count = cursor.fetchone()[0]
    print(f"📊 Anzahl Milestones: {milestone_count}")
    
    if milestone_count > 0:
        cursor.execute("SELECT id, title, status FROM milestones")
        milestones = cursor.fetchall()
        print("📋 Alle Milestones:")
        for milestone in milestones:
            print(f"  • ID: {milestone[0]}, Titel: {milestone[1]}, Status: {milestone[2]}")
    
    # 6. Prüfe Projekte
    cursor.execute("SELECT COUNT(*) FROM projects")
    project_count = cursor.fetchone()[0]
    print(f"📊 Anzahl Projekte: {project_count}")
    
    if project_count > 0:
        cursor.execute("SELECT id, name, status FROM projects")
        projects = cursor.fetchall()
        print("📋 Alle Projekte:")
        for project in projects:
            print(f"  • ID: {project[0]}, Name: {project[1]}, Status: {project[2]}")
    
    # 7. Prüfe Users
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"📊 Anzahl Benutzer: {user_count}")
    
    if user_count > 0:
        cursor.execute("SELECT id, email, user_type FROM users")
        users = cursor.fetchall()
        print("📋 Alle Benutzer:")
        for user in users:
            print(f"  • ID: {user[0]}, Email: {user[1]}, Typ: {user[2]}")
    
    conn.close()
    print("\n🎉 Datenbank-Überprüfung abgeschlossen!")

if __name__ == "__main__":
    check_quotes_database() 