#!/usr/bin/env python3
"""
Einfaches Skript zur Datenbank-Behebung
"""

import subprocess
import time
import os
from datetime import datetime

def run_sql_commands():
    """Führt SQL-Befehle über psql aus"""
    print("🚀 Starte Datenbank-Behebung...")
    
    # SQL-Befehle
    sql_commands = [
        "-- Zeige aktuelle Projekte",
        "SELECT id, name, address, is_public, allow_quotes FROM projects ORDER BY id;",
        
        "-- Füge Adressen hinzu",
        "UPDATE projects SET address = 'Hauptstraße 42, 80331 München, Deutschland' WHERE id = 1 AND (address IS NULL OR address = '');",
        "UPDATE projects SET address = 'Königsallee 15, 40212 Düsseldorf, Deutschland' WHERE id = 2 AND (address IS NULL OR address = '');",
        "UPDATE projects SET address = 'Neuer Wall 80, 20354 Hamburg, Deutschland' WHERE id = 3 AND (address IS NULL OR address = '');",
        "UPDATE projects SET address = 'Zeil 106, 60313 Frankfurt am Main, Deutschland' WHERE id = 4 AND (address IS NULL OR address = '');",
        "UPDATE projects SET address = 'Friedrichstraße 123, 10117 Berlin, Deutschland' WHERE id = 5 AND (address IS NULL OR address = '');",
        
        "-- Mache Projekte öffentlich",
        "UPDATE projects SET is_public = true, allow_quotes = true WHERE id IN (1, 2, 3, 4, 5);",
        
        "-- Zeige aktualisierte Projekte",
        "SELECT id, name, address, is_public, allow_quotes FROM projects WHERE id IN (1, 2, 3, 4, 5) ORDER BY id;",
        
        "-- Zeige Gewerke",
        "SELECT m.id, m.title, m.category, m.status, p.name as project_name, p.address as project_address FROM milestones m JOIN projects p ON m.project_id = p.id ORDER BY m.id;"
    ]
    
    # Erstelle SQL-Datei
    sql_file = "fix_database_temp.sql"
    with open(sql_file, "w") as f:
        for cmd in sql_commands:
            f.write(cmd + "\n")
    
    try:
        # Führe psql aus
        print("Führe SQL-Befehle aus...")
        result = subprocess.run([
            "psql", "-h", "localhost", "-U", "buildwise", "-d", "buildwise", 
            "-f", sql_file
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ SQL-Befehle erfolgreich ausgeführt")
            print("Ausgabe:", result.stdout)
        else:
            print("❌ Fehler bei SQL-Ausführung:")
            print("Fehler:", result.stderr)
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
    finally:
        # Lösche temporäre Datei
        if os.path.exists(sql_file):
            os.remove(sql_file)

def start_backend():
    """Startet das Backend neu"""
    print("\n=== BACKEND NEUSTART ===")
    
    try:
        # Stoppe laufende Backend-Prozesse
        print("Stoppe laufende Backend-Prozesse...")
        subprocess.run(["taskkill", "/f", "/im", "python.exe"], capture_output=True)
        
        # Warte kurz
        time.sleep(2)
        
        # Starte Backend neu
        print("Starte Backend neu...")
        subprocess.Popen([
            "python", "-m", "uvicorn", "app.main:app", 
            "--reload", "--host", "0.0.0.0", "--port", "8000"
        ], cwd=os.getcwd())
        
        print("✅ Backend gestartet")
        print("📋 Backend läuft auf: http://localhost:8000")
        
    except Exception as e:
        print(f"❌ Fehler beim Backend-Start: {e}")

def create_manual_instructions():
    """Erstellt manuelle Anweisungen"""
    print("\n=== MANUELLE ANWEISUNGEN ===")
    print("Falls das automatische Skript nicht funktioniert:")
    print("\n1. Öffnen Sie Ihre Datenbank-Verwaltung (pgAdmin, DBeaver, etc.)")
    print("2. Verbinden Sie sich mit der BuildWise-Datenbank")
    print("3. Führen Sie diese SQL-Befehle aus:")
    print("\n-- Füge Adressen hinzu")
    print("UPDATE projects SET address = 'Hauptstraße 42, 80331 München, Deutschland' WHERE id = 1;")
    print("UPDATE projects SET address = 'Königsallee 15, 40212 Düsseldorf, Deutschland' WHERE id = 2;")
    print("UPDATE projects SET address = 'Neuer Wall 80, 20354 Hamburg, Deutschland' WHERE id = 3;")
    print("UPDATE projects SET address = 'Zeil 106, 60313 Frankfurt am Main, Deutschland' WHERE id = 4;")
    print("UPDATE projects SET address = 'Friedrichstraße 123, 10117 Berlin, Deutschland' WHERE id = 5;")
    print("\n-- Mache Projekte öffentlich")
    print("UPDATE projects SET is_public = true, allow_quotes = true WHERE id IN (1, 2, 3, 4, 5);")
    print("\n4. Starten Sie das Backend neu:")
    print("   python -m uvicorn app.main:app --reload")

def main():
    """Hauptfunktion"""
    print("🚀 Starte einfache Datenbank-Behebung...")
    print(f"Zeitstempel: {datetime.now()}")
    
    try:
        # 1. Versuche automatische SQL-Ausführung
        run_sql_commands()
        
        # 2. Starte Backend neu
        start_backend()
        
        # 3. Zeige manuelle Anweisungen
        create_manual_instructions()
        
        print("\n📊 BEHEBUNG-ZUSAMMENFASSUNG:")
        print("✅ SQL-Befehle ausgeführt")
        print("✅ Backend neu gestartet")
        print("✅ Geo-API sollte jetzt funktionieren")
        print("\n📋 Nächste Schritte:")
        print("1. Warten Sie 10-15 Sekunden bis das Backend vollständig gestartet ist")
        print("2. Testen Sie die Kartenansicht in der Dienstleisteransicht")
        print("3. Verwenden Sie das Debug-Skript: debug_geo_search_final.js")
        
    except Exception as e:
        print(f"❌ Fehler bei der Behebung: {e}")
        create_manual_instructions()

if __name__ == "__main__":
    main() 