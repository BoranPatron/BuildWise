#!/usr/bin/env python3
import sqlite3

def check_quotes_and_projects():
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    print("🔍 Überprüfe Quotes und Projekt-Zuordnungen...")
    
    # Check alle Quotes
    cursor.execute('''
        SELECT q.id, q.service_provider_id, q.milestone_id, q.status,
               u.first_name, u.last_name, u.user_type,
               m.name as milestone_name, p.id as project_id, p.name as project_name
        FROM quotes q
        JOIN users u ON q.service_provider_id = u.id
        JOIN milestones m ON q.milestone_id = m.id
        JOIN projects p ON m.project_id = p.id
        ORDER BY q.id
    ''')
    
    quotes = cursor.fetchall()
    print(f"📋 {len(quotes)} Quotes gefunden:")
    for quote in quotes:
        quote_id, sp_id, milestone_id, status, first_name, last_name, user_type, milestone_name, project_id, project_name = quote
        print(f"  Quote {quote_id}: Service Provider {sp_id} ({first_name} {last_name})")
        print(f"    Status: {status}")
        print(f"    Milestone: {milestone_id} ({milestone_name})")
        print(f"    Projekt: {project_id} ({project_name})")
        print("    ---")
    
    print()
    
    # Check welche Projekte User 6 (Dienstleister) sehen sollte
    user_id = 6
    print(f"👤 User {user_id} sollte folgende Projekte sehen:")
    
    # Eigene Projekte
    cursor.execute('SELECT id, name FROM projects WHERE owner_id = ?', (user_id,))
    owned = cursor.fetchall()
    print(f"  Eigene Projekte: {len(owned)}")
    for proj in owned:
        print(f"    - Projekt {proj[0]}: {proj[1]}")
    
    # Projekte über Quotes
    cursor.execute('''
        SELECT DISTINCT p.id, p.name
        FROM projects p
        JOIN milestones m ON p.id = m.project_id
        JOIN quotes q ON m.id = q.milestone_id
        WHERE q.service_provider_id = ?
    ''', (user_id,))
    
    involved = cursor.fetchall()
    print(f"  Beteiligte Projekte (über Quotes): {len(involved)}")
    for proj in involved:
        print(f"    - Projekt {proj[0]}: {proj[1]}")
    
    print()
    print(f"📊 User {user_id} sollte insgesamt {len(owned) + len(involved)} Projekte sehen")
    
    conn.close()

if __name__ == "__main__":
    check_quotes_and_projects()