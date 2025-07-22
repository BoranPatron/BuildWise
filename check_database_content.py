#!/usr/bin/env python3
"""
Überprüft den Inhalt der Datenbank
"""

import sqlite3
import os

def check_database():
    """Überprüft den Datenbank-Inhalt"""
    print("🔍 DATENBANK-INHALT ÜBERPRÜFUNG")
    print("=" * 40)
    
    db_path = "buildwise.db"
    if not os.path.exists(db_path):
        print("❌ Datenbank nicht gefunden:", db_path)
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n📊 TABELLEN-ÜBERSICHT:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   📋 {table_name}: {count} Einträge")
        
        print("\n👤 USERS:")
        cursor.execute("SELECT id, email, user_type FROM users LIMIT 10")
        users = cursor.fetchall()
        for user in users:
            print(f"   - ID {user[0]}: {user[1]} (Typ: {user[2]})")
        
        print("\n📊 PROJECTS:")
        cursor.execute("SELECT id, name, owner_id FROM projects LIMIT 10")
        projects = cursor.fetchall()
        for project in projects:
            print(f"   - ID {project[0]}: {project[1]} (Owner: {project[2]})")
        
        print("\n🎯 MILESTONES:")
        cursor.execute("SELECT id, title, project_id FROM milestones LIMIT 10")
        milestones = cursor.fetchall()
        for milestone in milestones:
            print(f"   - ID {milestone[0]}: {milestone[1]} (Project: {milestone[2]})")
        
        print("\n💰 QUOTES:")
        cursor.execute("SELECT id, title, project_id FROM quotes LIMIT 10")
        quotes = cursor.fetchall()
        for quote in quotes:
            print(f"   - ID {quote[0]}: {quote[1]} (Project: {quote[2]})")
        
        conn.close()
        print("\n✅ Datenbank-Überprüfung abgeschlossen")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    check_database() 