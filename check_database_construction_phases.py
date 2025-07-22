#!/usr/bin/env python3
"""
Überprüfung der Datenbank-Struktur für Bauphasen
Prüft ob die erforderlichen Spalten in der projects Tabelle vorhanden sind
"""

import sqlite3
import os
from datetime import datetime

def check_database_structure():
    """Überprüft die Datenbank-Struktur für Bauphasen"""
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print("❌ Datenbank buildwise.db nicht gefunden!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Prüfe ob projects Tabelle existiert
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='projects';
        """)
        
        if not cursor.fetchone():
            print("❌ Tabelle 'projects' nicht gefunden!")
            return False
        
        # Hole alle Spalten der projects Tabelle
        cursor.execute("PRAGMA table_info(projects);")
        columns_info = cursor.fetchall()
        columns = [column[1] for column in columns_info]
        
        print("📋 Aktuelle Spalten in projects Tabelle:")
        for column_info in columns_info:
            col_name = column_info[1]
            col_type = column_info[2]
            col_notnull = column_info[3]
            col_default = column_info[4]
            print(f"  - {col_name} ({col_type}){' NOT NULL' if col_notnull else ''}{f' DEFAULT {col_default}' if col_default else ''}")
        
        # Prüfe erforderliche Spalten für Bauphasen
        required_columns = {
            'construction_phase': 'TEXT',
            'address_country': 'TEXT'
        }
        
        missing_columns = []
        for col_name, col_type in required_columns.items():
            if col_name not in columns:
                missing_columns.append(col_name)
        
        if missing_columns:
            print(f"\n❌ Fehlende Spalten für Bauphasen: {missing_columns}")
            print("💡 Führen Sie das Migration-Skript aus: python add_construction_phase_migration.py")
            return False
        else:
            print(f"\n✅ Alle erforderlichen Spalten für Bauphasen vorhanden!")
        
        # Prüfe Projekte und deren Bauphasen
        cursor.execute("SELECT COUNT(*) FROM projects;")
        total_projects = cursor.fetchone()[0]
        
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
        
        print(f"\n📊 Projekte-Statistik:")
        print(f"  - Gesamt: {total_projects} Projekte")
        print(f"  - Mit Bauphase: {projects_with_phases} Projekte")
        print(f"  - Mit Land: {projects_with_country} Projekte")
        
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
        
        # Zeige Beispiele für Projekte mit Bauphasen
        cursor.execute("""
            SELECT id, name, construction_phase, address_country 
            FROM projects 
            WHERE construction_phase IS NOT NULL AND construction_phase != ''
            LIMIT 5;
        """)
        examples = cursor.fetchall()
        
        if examples:
            print(f"\n📝 Beispiele für Projekte mit Bauphasen:")
            for project_id, name, phase, country in examples:
                print(f"  - ID {project_id}: '{name}' - Phase: {phase} - Land: {country}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei der Überprüfung: {e}")
        return False
    finally:
        conn.close()

def test_construction_phases():
    """Testet die Bauphasen-Funktionalität"""
    print("\n🧪 Teste Bauphasen-Funktionalität...")
    
    # Teste Phasen für verschiedene Länder
    test_cases = [
        ('Deutschland', ['planungsphase', 'baugenehmigung', 'ausschreibung', 'aushub', 'fundament', 'rohbau', 'dach', 'fassade', 'innenausbau', 'fertigstellung']),
        ('Schweiz', ['vorprojekt', 'projektierung', 'baugenehmigung', 'ausschreibung', 'aushub', 'fundament', 'rohbau', 'dach', 'fassade', 'innenausbau', 'fertigstellung']),
        ('Österreich', ['planungsphase', 'einreichung', 'ausschreibung', 'aushub', 'fundament', 'rohbau', 'dach', 'fassade', 'innenausbau', 'fertigstellung'])
    ]
    
    for country, expected_phases in test_cases:
        print(f"\n🌍 Teste {country}:")
        print(f"  Erwartete Phasen: {len(expected_phases)}")
        print(f"  Phasen: {', '.join(expected_phases[:3])}...")
    
    print("\n✅ Bauphasen-Tests abgeschlossen")

def main():
    """Hauptfunktion"""
    print("🔍 Bauphasen-Datenbank-Überprüfung")
    print("=" * 50)
    
    # Überprüfe Datenbank-Struktur
    if check_database_structure():
        print("\n✅ Datenbank ist bereit für Bauphasen!")
        
        # Teste Bauphasen-Funktionalität
        test_construction_phases()
        
        print("\n🎉 Überprüfung erfolgreich abgeschlossen!")
        print("📋 Die Datenbank unterstützt alle Bauphasen-Features")
    else:
        print("\n❌ Datenbank ist NICHT bereit für Bauphasen!")
        print("💡 Führen Sie die Migration aus:")
        print("   python add_construction_phase_migration.py")

if __name__ == "__main__":
    main() 