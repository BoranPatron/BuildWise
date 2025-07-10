#!/usr/bin/env python3
"""
Skript zum Öffentlich-Machen von Projekten für Dienstleister
"""

import sqlite3
import sys

def make_project_public(project_id: int):
    """Macht ein Projekt öffentlich für Dienstleister"""
    try:
        conn = sqlite3.connect('buildwise.db')
        cursor = conn.cursor()
        
        # Prüfe ob Projekt existiert
        cursor.execute("SELECT id, name, is_public, allow_quotes FROM projects WHERE id = ?", (project_id,))
        project = cursor.fetchone()
        
        if not project:
            print(f"❌ Projekt {project_id} nicht gefunden!")
            return False
        
        print(f"🔍 Projekt gefunden:")
        print(f"  ID: {project[0]}")
        print(f"  Name: {project[1]}")
        print(f"  Ist öffentlich: {project[2]}")
        print(f"  Erlaubt Angebote: {project[3]}")
        
        # Mache Projekt öffentlich
        cursor.execute("""
            UPDATE projects 
            SET is_public = 1, allow_quotes = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (project_id,))
        
        conn.commit()
        
        # Prüfe das Update
        cursor.execute("SELECT id, name, is_public, allow_quotes FROM projects WHERE id = ?", (project_id,))
        updated_project = cursor.fetchone()
        
        print(f"\n✅ Projekt erfolgreich aktualisiert:")
        print(f"  ID: {updated_project[0]}")
        print(f"  Name: {updated_project[1]}")
        print(f"  Ist öffentlich: {updated_project[2]}")
        print(f"  Erlaubt Angebote: {updated_project[3]}")
        
        # Zeige alle Milestones des Projekts
        cursor.execute("""
            SELECT id, title, status, project_id 
            FROM milestones 
            WHERE project_id = ?
        """, (project_id,))
        
        milestones = cursor.fetchall()
        print(f"\n📋 Milestones für Projekt {project_id}:")
        for milestone in milestones:
            print(f"  - ID: {milestone[0]}, Titel: '{milestone[1]}', Status: '{milestone[2]}'")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Aktualisieren des Projekts: {e}")
        return False

def main():
    """Hauptfunktion"""
    print("🔧 Projekt öffentlich machen für Dienstleister")
    print("=" * 50)
    
    project_id = 4  # Projekt 4 (Hausbau Boran)
    
    print(f"🎯 Mache Projekt {project_id} öffentlich...")
    
    success = make_project_public(project_id)
    
    if success:
        print(f"\n✅ Projekt {project_id} ist jetzt öffentlich!")
        print("💡 Dienstleister sollten jetzt die Milestones sehen können.")
    else:
        print(f"\n❌ Fehler beim Öffentlich-Machen von Projekt {project_id}")

if __name__ == "__main__":
    main() 