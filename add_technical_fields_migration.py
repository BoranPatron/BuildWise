#!/usr/bin/env python3
"""
Manuelle Migration: Füge technische Felder zu milestones Tabelle hinzu
"""

import psycopg2
import os
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

# Datenbankverbindung
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://buildwise:buildwise@localhost:5432/buildwise")

def add_technical_fields():
    """Füge technische Felder zur milestones Tabelle hinzu"""
    
    conn = None
    try:
        # Verbindung zur Datenbank
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("🔧 Füge technische Felder zur milestones Tabelle hinzu...")
        
        # Prüfe ob Felder bereits existieren
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'milestones' 
            AND column_name IN ('technical_specifications', 'quality_requirements', 'safety_requirements', 'environmental_requirements', 'category_specific_fields')
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"📋 Bestehende Felder: {existing_columns}")
        
        # Füge fehlende Felder hinzu
        fields_to_add = [
            ("technical_specifications", "TEXT"),
            ("quality_requirements", "TEXT"),
            ("safety_requirements", "TEXT"),
            ("environmental_requirements", "TEXT"),
            ("category_specific_fields", "TEXT")
        ]
        
        for field_name, field_type in fields_to_add:
            if field_name not in existing_columns:
                print(f"➕ Füge Feld '{field_name}' hinzu...")
                cursor.execute(f"ALTER TABLE milestones ADD COLUMN {field_name} {field_type}")
            else:
                print(f"✅ Feld '{field_name}' existiert bereits")
        
        # Commit Änderungen
        conn.commit()
        print("✅ Migration erfolgreich abgeschlossen!")
        
    except Exception as e:
        print(f"❌ Fehler bei der Migration: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_technical_fields() 