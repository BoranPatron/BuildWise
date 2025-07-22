#!/usr/bin/env python3
"""
Migration-Skript für Bauphasen-Funktionalität
Fügt construction_phase und address_country Felder zur projects Tabelle hinzu
"""

import sqlite3
import os
from datetime import datetime

def check_database_structure():
    """Überprüft die aktuelle Datenbank-Struktur"""
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print("❌ Datenbank buildwise.db nicht gefunden!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Prüfe ob projects Tabelle existiert
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='projects';
    """)
    
    if not cursor.fetchone():
        print("❌ Tabelle 'projects' nicht gefunden!")
        conn.close()
        return False
    
    # Prüfe aktuelle Spalten
    cursor.execute("PRAGMA table_info(projects);")
    columns = [column[1] for column in cursor.fetchall()]
    
    print("📋 Aktuelle Spalten in projects Tabelle:")
    for column in columns:
        print(f"  - {column}")
    
    conn.close()
    return True

def add_construction_phase_columns():
    """Fügt construction_phase und address_country Spalten hinzu"""
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print("❌ Datenbank buildwise.db nicht gefunden!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Prüfe ob construction_phase Spalte bereits existiert
        cursor.execute("PRAGMA table_info(projects);")
        columns = [column[1] for column in cursor.fetchall()]
        
        changes_made = False
        
        # Füge construction_phase Spalte hinzu falls nicht vorhanden
        if 'construction_phase' not in columns:
            print("➕ Füge construction_phase Spalte hinzu...")
            cursor.execute("""
                ALTER TABLE projects 
                ADD COLUMN construction_phase TEXT;
            """)
            changes_made = True
            print("✅ construction_phase Spalte hinzugefügt")
        else:
            print("✅ construction_phase Spalte bereits vorhanden")
        
        # Füge address_country Spalte hinzu falls nicht vorhanden
        if 'address_country' not in columns:
            print("➕ Füge address_country Spalte hinzu...")
            cursor.execute("""
                ALTER TABLE projects 
                ADD COLUMN address_country TEXT DEFAULT 'Deutschland';
            """)
            changes_made = True
            print("✅ address_country Spalte hinzugefügt")
        else:
            print("✅ address_country Spalte bereits vorhanden")
        
        # Commit Änderungen
        conn.commit()
        
        if changes_made:
            print("✅ Datenbank-Migration erfolgreich abgeschlossen!")
        else:
            print("ℹ️ Keine Änderungen erforderlich - alle Spalten bereits vorhanden")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei der Migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def update_existing_projects():
    """Aktualisiert bestehende Projekte mit Standardwerten"""
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print("❌ Datenbank buildwise.db nicht gefunden!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Zähle Projekte ohne address_country
        cursor.execute("""
            SELECT COUNT(*) FROM projects 
            WHERE address_country IS NULL OR address_country = '';
        """)
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"🔄 Aktualisiere {count} Projekte mit Standard-Land...")
            cursor.execute("""
                UPDATE projects 
                SET address_country = 'Deutschland' 
                WHERE address_country IS NULL OR address_country = '';
            """)
            conn.commit()
            print("✅ Bestehende Projekte aktualisiert")
        else:
            print("ℹ️ Alle Projekte haben bereits ein Land gesetzt")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Aktualisieren der Projekte: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def verify_migration():
    """Überprüft die Migration"""
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print("❌ Datenbank buildwise.db nicht gefunden!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Prüfe finale Spalten
        cursor.execute("PRAGMA table_info(projects);")
        columns = [column[1] for column in cursor.fetchall()]
        
        required_columns = ['construction_phase', 'address_country']
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            print(f"❌ Fehlende Spalten: {missing_columns}")
            return False
        
        print("✅ Alle erforderlichen Spalten vorhanden:")
        for col in required_columns:
            print(f"  - {col}")
        
        # Prüfe Projekte
        cursor.execute("SELECT COUNT(*) FROM projects;")
        project_count = cursor.fetchone()[0]
        print(f"📊 Anzahl Projekte in der Datenbank: {project_count}")
        
        # Prüfe Länder-Verteilung
        cursor.execute("""
            SELECT address_country, COUNT(*) 
            FROM projects 
            GROUP BY address_country;
        """)
        countries = cursor.fetchall()
        
        print("🌍 Länder-Verteilung:")
        for country, count in countries:
            print(f"  - {country or 'Nicht gesetzt'}: {count} Projekte")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei der Verifikation: {e}")
        return False
    finally:
        conn.close()

def main():
    """Hauptfunktion für die Migration"""
    print("🏗️ Bauphasen-Datenbank-Migration")
    print("=" * 50)
    
    # Schritt 1: Struktur prüfen
    print("\n1️⃣ Überprüfe Datenbank-Struktur...")
    if not check_database_structure():
        print("❌ Migration abgebrochen - Datenbank-Struktur nicht korrekt")
        return
    
    # Schritt 2: Spalten hinzufügen
    print("\n2️⃣ Füge Bauphasen-Spalten hinzu...")
    if not add_construction_phase_columns():
        print("❌ Migration abgebrochen - Fehler beim Hinzufügen der Spalten")
        return
    
    # Schritt 3: Bestehende Projekte aktualisieren
    print("\n3️⃣ Aktualisiere bestehende Projekte...")
    if not update_existing_projects():
        print("❌ Migration abgebrochen - Fehler beim Aktualisieren der Projekte")
        return
    
    # Schritt 4: Verifikation
    print("\n4️⃣ Überprüfe Migration...")
    if not verify_migration():
        print("❌ Migration fehlgeschlagen - Verifikation fehlgeschlagen")
        return
    
    print("\n🎉 Migration erfolgreich abgeschlossen!")
    print("✅ Die Datenbank ist bereit für die Bauphasen-Funktionalität")
    print("\n📋 Nächste Schritte:")
    print("  1. Starten Sie den Backend-Server neu")
    print("  2. Testen Sie die Bauphasen-Funktionalität im Frontend")
    print("  3. Erstellen Sie ein neues Projekt mit Bauphasen")

if __name__ == "__main__":
    main() 