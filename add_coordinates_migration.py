#!/usr/bin/env python3

"""
Migration: Koordinaten-Spalten zu resources Tabelle hinzufügen
Fügt latitude und longitude Spalten zur bestehenden resources Tabelle hinzu.
"""

import sqlite3
import sys
from datetime import datetime

def add_coordinate_columns(conn):
    """Füge latitude und longitude Spalten zur resources Tabelle hinzu"""
    
    cursor = conn.cursor()
    
    print("🔧 Füge Koordinaten-Spalten zur resources Tabelle hinzu...")
    
    # Prüfe ob die Spalten bereits existieren
    cursor.execute("PRAGMA table_info(resources)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    print(f"📋 Bestehende Spalten: {', '.join(column_names)}")
    
    # Füge latitude Spalte hinzu falls nicht vorhanden
    if 'latitude' not in column_names:
        try:
            cursor.execute("ALTER TABLE resources ADD COLUMN latitude DECIMAL(10,8)")
            print("✅ latitude Spalte hinzugefügt")
        except sqlite3.Error as e:
            print(f"⚠️  latitude Spalte bereits vorhanden oder Fehler: {e}")
    else:
        print("ℹ️  latitude Spalte bereits vorhanden")
    
    # Füge longitude Spalte hinzu falls nicht vorhanden
    if 'longitude' not in column_names:
        try:
            cursor.execute("ALTER TABLE resources ADD COLUMN longitude DECIMAL(11,8)")
            print("✅ longitude Spalte hinzugefügt")
        except sqlite3.Error as e:
            print(f"⚠️  longitude Spalte bereits vorhanden oder Fehler: {e}")
    else:
        print("ℹ️  longitude Spalte bereits vorhanden")
    
    # Erstelle Index für Geo-Suche falls nicht vorhanden
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resources_location ON resources(latitude, longitude)")
        print("✅ Geo-Index erstellt")
    except sqlite3.Error as e:
        print(f"⚠️  Geo-Index Fehler: {e}")
    
    conn.commit()
    print("✅ Koordinaten-Spalten Migration abgeschlossen!")

def verify_migration(conn):
    """Verifiziere die Migration"""
    cursor = conn.cursor()
    
    print("\n🔍 Verifikation der Migration:")
    
    # Prüfe Tabellenstruktur
    cursor.execute("PRAGMA table_info(resources)")
    columns = cursor.fetchall()
    
    print("📊 Aktuelle resources Tabelle Spalten:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # Prüfe ob Koordinaten-Spalten vorhanden sind
    column_names = [col[1] for col in columns]
    has_latitude = 'latitude' in column_names
    has_longitude = 'longitude' in column_names
    
    print(f"\n📍 Koordinaten-Spalten Status:")
    print(f"  - latitude: {'✅' if has_latitude else '❌'}")
    print(f"  - longitude: {'✅' if has_longitude else '❌'}")
    
    if has_latitude and has_longitude:
        print("\n🎉 Migration erfolgreich! Koordinaten-Spalten sind verfügbar.")
        
        # Zeige aktuelle Ressourcen mit Koordinaten
        cursor.execute("SELECT id, address_city, latitude, longitude FROM resources LIMIT 5")
        resources = cursor.fetchall()
        
        print("\n📋 Beispiel-Ressourcen:")
        for resource in resources:
            print(f"  ID {resource[0]}: {resource[1]} - lat: {resource[2]}, lon: {resource[3]}")
    else:
        print("\n❌ Migration fehlgeschlagen! Koordinaten-Spalten fehlen.")

def main():
    """Hauptfunktion für die Koordinaten-Migration"""
    
    print("🚀 Starte Koordinaten-Spalten Migration...")
    print(f"📅 Zeitstempel: {datetime.now()}")
    
    # Verbinde zur Datenbank
    try:
        conn = sqlite3.connect('buildwise.db')
        print("✅ Datenbankverbindung hergestellt")
        
        # Führe Migration aus
        add_coordinate_columns(conn)
        
        # Verifiziere Migration
        verify_migration(conn)
        
    except sqlite3.Error as e:
        print(f"❌ Datenbankfehler: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()
            print("🔐 Datenbankverbindung geschlossen")

if __name__ == "__main__":
    main()
