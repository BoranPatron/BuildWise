#!/usr/bin/env python3
"""
Überprüfung der Bauphasen-Daten in der Datenbank
Prüft ob die construction_phase und address_country Felder korrekt gesetzt sind
"""

import sqlite3
import os
from datetime import datetime

def check_project_construction_phases():
    """Überprüft die Bauphasen-Daten in der Datenbank"""
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print("❌ Datenbank buildwise.db nicht gefunden!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Prüfe alle Projekte
        cursor.execute("""
            SELECT id, name, construction_phase, address_country, project_type, status
            FROM projects
            ORDER BY id;
        """)
        projects = cursor.fetchall()
        
        print("📋 Projekte in der Datenbank:")
        print("=" * 80)
        
        for project in projects:
            project_id, name, construction_phase, address_country, project_type, status = project
            
            print(f"ID: {project_id}")
            print(f"Name: {name}")
            print(f"Construction Phase: {construction_phase or 'NICHT GESETZT'}")
            print(f"Address Country: {address_country or 'NICHT GESETZT'}")
            print(f"Project Type: {project_type}")
            print(f"Status: {status}")
            print("-" * 40)
        
        # Zähle Projekte mit Bauphasen
        cursor.execute("""
            SELECT COUNT(*) FROM projects 
            WHERE construction_phase IS NOT NULL AND construction_phase != '';
        """)
        projects_with_phases = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM projects 
            WHERE address_country IS NOT NULL AND address_country != '';
        """)
        projects_with_country = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM projects;")
        total_projects = cursor.fetchone()[0]
        
        print(f"\n📊 Statistik:")
        print(f"  - Gesamt Projekte: {total_projects}")
        print(f"  - Mit Bauphase: {projects_with_phases}")
        print(f"  - Mit Land: {projects_with_country}")
        
        # Zeige Bauphasen-Verteilung
        cursor.execute("""
            SELECT construction_phase, COUNT(*) 
            FROM projects 
            WHERE construction_phase IS NOT NULL AND construction_phase != ''
            GROUP BY construction_phase;
        """)
        phases = cursor.fetchall()
        
        if phases:
            print(f"\n🏗️ Bauphasen-Verteilung:")
            for phase, count in phases:
                print(f"  - {phase}: {count} Projekte")
        
        # Zeige Länder-Verteilung
        cursor.execute("""
            SELECT address_country, COUNT(*) 
            FROM projects 
            WHERE address_country IS NOT NULL AND address_country != ''
            GROUP BY address_country;
        """)
        countries = cursor.fetchall()
        
        if countries:
            print(f"\n🌍 Länder-Verteilung:")
            for country, count in countries:
                print(f"  - {country}: {count} Projekte")
        
        # Teste spezifische Bauphasen
        test_phases = ['innenausbau', 'rohbau', 'fundament', 'planungsphase']
        print(f"\n🧪 Teste spezifische Bauphasen:")
        
        for phase in test_phases:
            cursor.execute("""
                SELECT id, name, address_country 
                FROM projects 
                WHERE construction_phase = ?;
            """, (phase,))
            results = cursor.fetchall()
            
            if results:
                print(f"  ✅ '{phase}' gefunden in {len(results)} Projekt(en):")
                for project_id, name, country in results:
                    print(f"    - ID {project_id}: '{name}' (Land: {country or 'Nicht gesetzt'})")
            else:
                print(f"  ❌ '{phase}' nicht gefunden")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei der Überprüfung: {e}")
        return False
    finally:
        conn.close()

def update_project_construction_phase():
    """Aktualisiert ein Projekt mit Bauphasen-Daten für Tests"""
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print("❌ Datenbank buildwise.db nicht gefunden!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Finde das erste Projekt
        cursor.execute("SELECT id, name FROM projects LIMIT 1;")
        project = cursor.fetchone()
        
        if not project:
            print("❌ Keine Projekte in der Datenbank gefunden!")
            return False
        
        project_id, project_name = project
        
        print(f"🔄 Aktualisiere Projekt ID {project_id}: '{project_name}'")
        
        # Setze Bauphasen-Daten
        cursor.execute("""
            UPDATE projects 
            SET construction_phase = 'innenausbau', 
                address_country = 'Deutschland'
            WHERE id = ?;
        """, (project_id,))
        
        conn.commit()
        
        # Überprüfe die Änderung
        cursor.execute("""
            SELECT id, name, construction_phase, address_country 
            FROM projects 
            WHERE id = ?;
        """, (project_id,))
        
        updated_project = cursor.fetchone()
        if updated_project:
            project_id, name, construction_phase, address_country = updated_project
            print(f"✅ Projekt aktualisiert:")
            print(f"  - ID: {project_id}")
            print(f"  - Name: {name}")
            print(f"  - Construction Phase: {construction_phase}")
            print(f"  - Address Country: {address_country}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Aktualisieren: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """Hauptfunktion"""
    print("🔍 Bauphasen-Datenbank-Überprüfung")
    print("=" * 50)
    
    # Überprüfe aktuelle Daten
    if check_project_construction_phases():
        print("\n✅ Überprüfung abgeschlossen!")
        
        # Frage nach Update
        response = input("\n🤔 Möchten Sie ein Projekt mit Test-Bauphasen aktualisieren? (j/n): ")
        if response.lower() in ['j', 'ja', 'y', 'yes']:
            if update_project_construction_phase():
                print("\n✅ Projekt erfolgreich aktualisiert!")
                print("\n🔄 Überprüfe erneut...")
                check_project_construction_phases()
            else:
                print("\n❌ Fehler beim Aktualisieren des Projekts!")
        else:
            print("\nℹ️ Keine Änderungen vorgenommen.")
    else:
        print("\n❌ Überprüfung fehlgeschlagen!")

if __name__ == "__main__":
    main() 