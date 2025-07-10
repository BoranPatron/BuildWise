#!/usr/bin/env python3
"""
Detailliertes Debug-Skript für Milestones
Zeigt alle Felder der Milestones an, um die Ursache für leere Arrays zu finden
"""

import os
import sys
import sqlite3
from datetime import datetime

# Pfad zur Datenbank
DB_PATH = 'buildwise.db'

def connect_db():
    """Verbindung zur Datenbank herstellen"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Ermöglicht Zugriff auf Spalten über Namen
        return conn
    except Exception as e:
        print(f"❌ Fehler beim Verbinden zur Datenbank: {e}")
        return None

def get_all_milestones_detailed():
    """Alle Milestones mit allen Feldern abrufen"""
    conn = connect_db()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        # Alle Milestones abrufen
        cursor.execute("""
            SELECT 
                m.*,
                p.name as project_name,
                p.status as project_status,
                p.is_public as project_is_public,
                p.allow_quotes as project_allow_quotes
            FROM milestones m
            LEFT JOIN projects p ON m.project_id = p.id
            ORDER BY m.id
        """)
        
        milestones = cursor.fetchall()
        
        print(f"🔍 Gefundene Milestones: {len(milestones)}")
        print("=" * 80)
        
        for i, milestone in enumerate(milestones, 1):
            print(f"\n📋 Milestone #{i} (ID: {milestone['id']})")
            print("-" * 50)
            
            # Alle Felder ausgeben
            for key in milestone.keys():
                value = milestone[key]
                if value is None:
                    value_str = "NULL"
                elif isinstance(value, str):
                    value_str = f'"{value}"'
                elif isinstance(value, (int, float)):
                    value_str = str(value)
                elif isinstance(value, bool):
                    value_str = "True" if value else "False"
                else:
                    value_str = str(value)
                
                print(f"  {key}: {value_str}")
            
            # Spezielle Analyse für Status
            status = milestone['status']
            print(f"\n  🔍 Status-Analyse:")
            print(f"    Status: '{status}' (Typ: {type(status)})")
            print(f"    Status == 'PLANNED': {status == 'PLANNED'}")
            print(f"    Status == 'IN_PROGRESS': {status == 'IN_PROGRESS'}")
            print(f"    Status in ['PLANNED', 'IN_PROGRESS']: {status in ['PLANNED', 'IN_PROGRESS']}")
            
            # Projekt-Status prüfen
            project_status = milestone['project_status']
            project_is_public = milestone['project_is_public']
            project_allow_quotes = milestone['project_allow_quotes']
            
            print(f"\n  🏗️  Projekt-Analyse:")
            print(f"    Projekt-ID: {milestone['project_id']}")
            print(f"    Projekt-Name: {milestone['project_name']}")
            print(f"    Projekt-Status: '{project_status}'")
            print(f"    Projekt ist öffentlich: {project_is_public}")
            print(f"    Projekt erlaubt Angebote: {project_allow_quotes}")
            
            # Soft-Delete prüfen
            if 'deleted_at' in milestone.keys():
                deleted_at = milestone['deleted_at']
                print(f"    Gelöscht am: {deleted_at}")
            
            print()
        
        return milestones
        
    except Exception as e:
        print(f"❌ Fehler beim Abrufen der Milestones: {e}")
        return []
    finally:
        conn.close()

def check_milestone_service_logic():
    """Logik des Milestone-Services simulieren"""
    print("\n🔧 Milestone-Service Logik simulieren")
    print("=" * 50)
    
    conn = connect_db()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Alle aktiven Milestones (PLANNED oder IN_PROGRESS)
        cursor.execute("""
            SELECT * FROM milestones 
            WHERE status IN ('PLANNED', 'IN_PROGRESS')
            AND (deleted_at IS NULL OR deleted_at = '')
        """)
        
        active_milestones = cursor.fetchall()
        print(f"✅ Aktive Milestones (PLANNED/IN_PROGRESS): {len(active_milestones)}")
        
        for milestone in active_milestones:
            print(f"  - ID: {milestone['id']}, Status: '{milestone['status']}', Projekt: {milestone['project_id']}")
        
        # Alle Milestones mit String-Vergleich
        cursor.execute("""
            SELECT * FROM milestones 
            WHERE status IN ('PLANNED', 'IN_PROGRESS')
        """)
        
        string_milestones = cursor.fetchall()
        print(f"\n✅ Milestones mit String-Vergleich: {len(string_milestones)}")
        
        for milestone in string_milestones:
            print(f"  - ID: {milestone['id']}, Status: '{milestone['status']}', Projekt: {milestone['project_id']}")
        
        # Alle Milestones ohne Filter
        cursor.execute("SELECT * FROM milestones")
        all_milestones = cursor.fetchall()
        print(f"\n📊 Alle Milestones: {len(all_milestones)}")
        
        # Status-Verteilung
        status_counts = {}
        for milestone in all_milestones:
            status = milestone['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("\n📈 Status-Verteilung:")
        for status, count in status_counts.items():
            print(f"  '{status}': {count}")
        
    except Exception as e:
        print(f"❌ Fehler bei der Service-Logik-Simulation: {e}")
    finally:
        conn.close()

def check_user_permissions():
    """Benutzer-Berechtigungen prüfen"""
    print("\n👤 Benutzer-Berechtigungen prüfen")
    print("=" * 50)
    
    conn = connect_db()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Dienstleister-User finden
        cursor.execute("""
            SELECT * FROM users 
            WHERE email LIKE '%dienstleister%' OR user_type = 'service_provider'
        """)
        
        service_providers = cursor.fetchall()
        print(f"🔍 Gefundene Dienstleister: {len(service_providers)}")
        
        for user in service_providers:
            print(f"\n  👤 Dienstleister:")
            print(f"    ID: {user['id']}")
            print(f"    E-Mail: {user['email']}")
            print(f"    Typ: {user['user_type']}")
            print(f"    Status: {user['status']}")
            print(f"    Aktiv: {user['is_active']}")
            print(f"    GDPR-Consent: {user['gdpr_consent']}")
            print(f"    Marketing-Consent: {user['marketing_consent']}")
            print(f"    Erstellt: {user['created_at']}")
            print(f"    Aktualisiert: {user['updated_at']}")
            
            if 'deleted_at' in user.keys():
                print(f"    Gelöscht: {user['deleted_at']}")
        
        # Projekte prüfen
        cursor.execute("SELECT * FROM projects WHERE id = 4")
        project_4 = cursor.fetchone()
        
        if project_4:
            print(f"\n  🏗️  Projekt 4:")
            for key in project_4.keys():
                print(f"    {key}: {project_4[key]}")
        else:
            print("\n  ❌ Projekt 4 nicht gefunden")
        
    except Exception as e:
        print(f"❌ Fehler bei der Benutzer-Prüfung: {e}")
    finally:
        conn.close()

def main():
    """Hauptfunktion"""
    print("🔍 Detaillierte Milestone-Analyse")
    print("=" * 80)
    print(f"📅 Zeitstempel: {datetime.now()}")
    print(f"🗄️  Datenbank: {DB_PATH}")
    print()
    
    # Prüfen ob Datenbank existiert
    if not os.path.exists(DB_PATH):
        print(f"❌ Datenbank {DB_PATH} nicht gefunden!")
        return
    
    # Alle Milestones mit Details
    milestones = get_all_milestones_detailed()
    
    # Service-Logik simulieren
    check_milestone_service_logic()
    
    # Benutzer-Berechtigungen prüfen
    check_user_permissions()
    
    print("\n" + "=" * 80)
    print("✅ Analyse abgeschlossen")
    print("💡 Überprüfen Sie die Ausgabe auf mögliche Ursachen für leere Arrays")

if __name__ == "__main__":
    main() 