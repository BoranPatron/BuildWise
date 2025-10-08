"""
Fügt Revisions-Felder zur quotes Tabelle hinzu für die Angebotsüberarbeitung nach Besichtigung
"""
import sqlite3
from pathlib import Path

# Datenbankpfad
db_path = Path(__file__).parent / "buildwise.db"

def add_revision_fields():
    """Fügt Revisions-Felder zur quotes Tabelle hinzu"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Prüfe ob Felder bereits existieren
        cursor.execute("PRAGMA table_info(quotes)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Fuege revised_after_inspection hinzu
        if 'revised_after_inspection' not in columns:
            print("+ Fuege Feld 'revised_after_inspection' hinzu...")
            cursor.execute("""
                ALTER TABLE quotes 
                ADD COLUMN revised_after_inspection BOOLEAN DEFAULT 0
            """)
            print("OK Feld 'revised_after_inspection' erfolgreich hinzugefuegt")
        else:
            print("INFO Feld 'revised_after_inspection' existiert bereits")
        
        # Fuege revision_count hinzu
        if 'revision_count' not in columns:
            print("+ Fuege Feld 'revision_count' hinzu...")
            cursor.execute("""
                ALTER TABLE quotes 
                ADD COLUMN revision_count INTEGER DEFAULT 0
            """)
            print("OK Feld 'revision_count' erfolgreich hinzugefuegt")
        else:
            print("INFO Feld 'revision_count' existiert bereits")
        
        # Fuege last_revised_at hinzu
        if 'last_revised_at' not in columns:
            print("+ Fuege Feld 'last_revised_at' hinzu...")
            cursor.execute("""
                ALTER TABLE quotes 
                ADD COLUMN last_revised_at TIMESTAMP
            """)
            print("OK Feld 'last_revised_at' erfolgreich hinzugefuegt")
        else:
            print("INFO Feld 'last_revised_at' existiert bereits")
        
        conn.commit()
        print("\nOK Alle Revisions-Felder erfolgreich hinzugefuegt/validiert")
        
    except Exception as e:
        print(f"ERROR Fehler beim Hinzufuegen der Felder: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Fuege Revisions-Felder zur quotes Tabelle hinzu...\n")
    add_revision_fields()

