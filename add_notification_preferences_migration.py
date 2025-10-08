"""
Migration: Notification Preferences Tabelle hinzufügen
Erstellt die notification_preferences Tabelle für die Benachrichtigungspräferenzen
"""
import sqlite3
import sys
from pathlib import Path

def run_migration():
    """Führt die Migration aus"""
    db_path = Path(__file__).parent / "buildwise.db"
    
    if not db_path.exists():
        print(f"Datenbank nicht gefunden: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("Pruefe ob notification_preferences Tabelle bereits existiert...")
        
        # Prüfe ob Tabelle existiert
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='notification_preferences'
        """)
        
        if cursor.fetchone():
            print("Tabelle notification_preferences existiert bereits")
            conn.close()
            return True
        
        print("Erstelle notification_preferences Tabelle...")
        
        # Erstelle Tabelle
        cursor.execute("""
            CREATE TABLE notification_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER NOT NULL UNIQUE,
                user_id INTEGER NOT NULL,
                service_provider_id INTEGER NOT NULL,
                enabled BOOLEAN NOT NULL DEFAULT 1,
                categories TEXT NOT NULL DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (service_provider_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Erstelle Indizes für Performance
        print("Erstelle Indizes...")
        
        cursor.execute("""
            CREATE INDEX idx_notification_preferences_contact_id 
            ON notification_preferences(contact_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_notification_preferences_user_id 
            ON notification_preferences(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_notification_preferences_service_provider_id 
            ON notification_preferences(service_provider_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_notification_preferences_enabled 
            ON notification_preferences(enabled)
        """)
        
        # Trigger für updated_at
        print("Erstelle Trigger fuer updated_at...")
        
        cursor.execute("""
            CREATE TRIGGER update_notification_preferences_timestamp 
            AFTER UPDATE ON notification_preferences
            BEGIN
                UPDATE notification_preferences 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END
        """)
        
        conn.commit()
        
        print("Migration erfolgreich abgeschlossen!")
        print("Tabelle notification_preferences erstellt")
        print("4 Indizes erstellt")
        print("1 Trigger erstellt")
        
        # Zeige Tabellenstruktur
        cursor.execute("PRAGMA table_info(notification_preferences)")
        columns = cursor.fetchall()
        
        print("\nTabellenstruktur:")
        for col in columns:
            print(f"   - {col[1]}: {col[2]}")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"Datenbankfehler: {e}")
        return False
    except Exception as e:
        print(f"Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Starte Migration: Notification Preferences")
    print("=" * 60)
    
    success = run_migration()
    
    print("=" * 60)
    if success:
        print("Migration erfolgreich!")
        sys.exit(0)
    else:
        print("Migration fehlgeschlagen!")
        sys.exit(1)

