#!/usr/bin/env python3
"""
Migration: Erweiterte Abnahme-Funktionalität
- Checkliste-Daten
- Wiedervorlage-System
- Foto-Annotation für Mängel
"""

import sqlite3
import json
from datetime import datetime

def run_migration():
    """Führt die Migration für erweiterte Abnahme-Funktionalität aus"""
    
    # Verbindung zur SQLite-Datenbank
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    try:
        print("🔄 Starte Migration: Erweiterte Abnahme-Funktionalität...")
        
        # 1. Erweitere acceptances Tabelle
        print("📋 Erweitere acceptances Tabelle...")
        
        # Prüfe ob Spalten bereits existieren
        cursor.execute("PRAGMA table_info(acceptances)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'checklist_data' not in columns:
            cursor.execute("ALTER TABLE acceptances ADD COLUMN checklist_data TEXT")
            print("✅ checklist_data Spalte hinzugefügt")
        
        if 'review_date' not in columns:
            cursor.execute("ALTER TABLE acceptances ADD COLUMN review_date DATE")
            print("✅ review_date Spalte hinzugefügt")
        
        if 'review_notes' not in columns:
            cursor.execute("ALTER TABLE acceptances ADD COLUMN review_notes TEXT")
            print("✅ review_notes Spalte hinzugefügt")
        
        # 2. Erweitere acceptance_defects Tabelle
        print("🔧 Erweitere acceptance_defects Tabelle...")
        
        cursor.execute("PRAGMA table_info(acceptance_defects)")
        defect_columns = [column[1] for column in cursor.fetchall()]
        
        if 'photo_annotations' not in defect_columns:
            cursor.execute("ALTER TABLE acceptance_defects ADD COLUMN photo_annotations TEXT")
            print("✅ photo_annotations Spalte hinzugefügt")
        
        # 3. Teste die neuen Strukturen
        print("🧪 Teste neue Strukturen...")
        
        # Prüfe ob neue Spalten verfügbar sind
        cursor.execute("PRAGMA table_info(acceptances)")
        acceptance_columns = [column[1] for column in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(acceptance_defects)")
        defect_columns = [column[1] for column in cursor.fetchall()]
        
        # Validiere neue Spalten
        required_acceptance_columns = ['checklist_data', 'review_date', 'review_notes']
        required_defect_columns = ['photo_annotations']
        
        for col in required_acceptance_columns:
            if col in acceptance_columns:
                print(f"✅ {col} Spalte erfolgreich hinzugefügt")
            else:
                raise Exception(f"❌ {col} Spalte fehlt")
        
        for col in required_defect_columns:
            if col in defect_columns:
                print(f"✅ {col} Spalte erfolgreich hinzugefügt")
            else:
                raise Exception(f"❌ {col} Spalte fehlt")
        
        print("✅ Strukturtest erfolgreich")
        
        # Migration abschließen
        conn.commit()
        print("✅ Migration erfolgreich abgeschlossen!")
        
        # Zusammenfassung
        print("\n📊 Migration Zusammenfassung:")
        print("   • Checkliste-Daten für Vor-Ort Prüfung hinzugefügt")
        print("   • Wiedervorlage-System für Abnahme unter Vorbehalt implementiert")
        print("   • Foto-Annotation für Mängel-Dokumentation aktiviert")
        print("   • Alle Tests erfolgreich")
        
    except Exception as e:
        print(f"❌ Fehler bei Migration: {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()