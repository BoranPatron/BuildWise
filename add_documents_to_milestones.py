"""
Migration: Dokumente-Feld zu Milestones hinzufügen
Datum: 2025-01-27
Beschreibung: Fügt ein JSON-Feld für Dokumente zur milestones Tabelle hinzu
"""

import sqlite3
import json
from datetime import datetime

def add_documents_field():
    """Fügt das documents Feld zur milestones Tabelle hinzu"""
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    try:
        print("🔧 Füge documents Feld zur milestones Tabelle hinzu...")
        
        # Prüfe ob das Feld bereits existiert
        cursor.execute("PRAGMA table_info(milestones)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'documents' not in columns:
            # Füge das documents Feld hinzu
            cursor.execute("""
                ALTER TABLE milestones 
                ADD COLUMN documents TEXT DEFAULT NULL
            """)
            print("✅ documents Feld erfolgreich hinzugefügt")
        else:
            print("ℹ️ documents Feld existiert bereits")
        
        conn.commit()
        print("✅ Migration erfolgreich abgeschlossen")
        
    except sqlite3.Error as e:
        print(f"❌ Fehler bei der Migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    add_documents_field() 