#!/usr/bin/env python3
"""
Überprüfung der milestones Tabelle
"""

import sqlite3
import os

def check_milestones_table():
    """Überprüft die milestones Tabelle"""
    print("🔍 Überprüfe milestones Tabelle...")
    
    if not os.path.exists('buildwise.db'):
        print("❌ Datenbank buildwise.db nicht gefunden!")
        return
    
    print("✅ Datenbank buildwise.db gefunden")
    
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    try:
        # Prüfe milestones Tabelle
        cursor.execute("SELECT COUNT(*) FROM milestones")
        milestones_count = cursor.fetchone()[0]
        print(f"📊 Milestones in der Datenbank: {milestones_count}")
        
        if milestones_count > 0:
            print("\n📋 Milestones Details:")
            cursor.execute("""
                SELECT id, title, description, status, priority, project_id, planned_date, created_at
                FROM milestones
                ORDER BY created_at DESC
                LIMIT 5
            """)
            milestones = cursor.fetchall()
            
            for milestone in milestones:
                print(f"  - ID {milestone[0]}: '{milestone[1]}' (Status: {milestone[3]}, Priorität: {milestone[4]}, Projekt: {milestone[5]})")
        
        # Prüfe quotes Tabelle
        cursor.execute("SELECT COUNT(*) FROM quotes")
        quotes_count = cursor.fetchone()[0]
        print(f"\n📊 Quotes in der Datenbank: {quotes_count}")
        
        # Prüfe cost_positions Tabelle
        cursor.execute("SELECT COUNT(*) FROM cost_positions")
        cost_positions_count = cursor.fetchone()[0]
        print(f"📊 CostPositions in der Datenbank: {cost_positions_count}")
        
        # Prüfe Projekte
        cursor.execute("SELECT COUNT(*) FROM projects")
        projects_count = cursor.fetchone()[0]
        print(f"📊 Projekte in der Datenbank: {projects_count}")
        
        if projects_count > 0:
            print("\n📋 Projekte Details:")
            cursor.execute("SELECT id, name, description FROM projects LIMIT 3")
            projects = cursor.fetchall()
            
            for project in projects:
                print(f"  - Projekt {project[0]}: '{project[1]}'")
        
        # Prüfe Verbindung zwischen Milestones und Projekten
        if milestones_count > 0 and projects_count > 0:
            print("\n🔗 Milestone-Projekt-Verbindung:")
            cursor.execute("""
                SELECT m.id, m.title, p.name as project_name
                FROM milestones m
                JOIN projects p ON m.project_id = p.id
                ORDER BY m.created_at DESC
                LIMIT 3
            """)
            connections = cursor.fetchall()
            
            for conn in connections:
                print(f"  - Milestone {conn[0]} ('{conn[1]}') -> Projekt: '{conn[2]}'")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Fehler bei der Überprüfung: {e}")
        import traceback
        traceback.print_exc()
        conn.close()

if __name__ == "__main__":
    check_milestones_table() 