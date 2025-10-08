#!/usr/bin/env python3
"""
Migration Script: Separate Notification States für Bauträger und Dienstleister

Problem: 
- Bauträger und Dienstleister teilen sich die gleiche has_unread_messages Spalte
- Wenn einer die Nachrichten als gelesen markiert, verliert der andere die Benachrichtigung

Lösung:
- has_unread_messages_bautraeger: Boolean für Bauträger-Benachrichtigungen
- has_unread_messages_dienstleister: Boolean für Dienstleister-Benachrichtigungen
- Alte has_unread_messages Spalte wird entfernt
"""

import sqlite3
import sys
import os

def migrate_notification_states():
    """Migriert die Notification-States zu separaten Spalten"""
    
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Datenbank {db_path} nicht gefunden!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Starte Migration: Separate Notification States...")
        
        # 1. Prüfe ob neue Spalten bereits existieren
        cursor.execute("PRAGMA table_info(milestones)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'has_unread_messages_bautraeger' in columns:
            print("Spalte has_unread_messages_bautraeger existiert bereits")
        else:
            # 2. Füge neue Spalten hinzu
            print("Füge has_unread_messages_bautraeger hinzu...")
            cursor.execute("ALTER TABLE milestones ADD COLUMN has_unread_messages_bautraeger BOOLEAN DEFAULT FALSE")
            
        if 'has_unread_messages_dienstleister' in columns:
            print("Spalte has_unread_messages_dienstleister existiert bereits")
        else:
            print("Füge has_unread_messages_dienstleister hinzu...")
            cursor.execute("ALTER TABLE milestones ADD COLUMN has_unread_messages_dienstleister BOOLEAN DEFAULT FALSE")
        
        # 3. Migriere bestehende Daten
        print("Migriere bestehende has_unread_messages Daten...")
        
        # Prüfe ob alte Spalte existiert
        if 'has_unread_messages' in columns:
            # Migriere Daten: Wenn has_unread_messages = True, setze beide neuen Spalten auf True
            cursor.execute("""
                UPDATE milestones 
                SET 
                    has_unread_messages_bautraeger = CASE WHEN has_unread_messages = 1 THEN 1 ELSE 0 END,
                    has_unread_messages_dienstleister = CASE WHEN has_unread_messages = 1 THEN 1 ELSE 0 END
                WHERE has_unread_messages IS NOT NULL
            """)
            
            affected_rows = cursor.rowcount
            print(f"{affected_rows} Milestones migriert")
            
            # 4. Entferne alte Spalte (optional - für jetzt behalten wir sie)
            # cursor.execute("ALTER TABLE milestones DROP COLUMN has_unread_messages")
            # print("Alte has_unread_messages Spalte entfernt")
        else:
            print("Alte has_unread_messages Spalte nicht gefunden - Migration übersprungen")
        
        # 5. Commit Änderungen
        conn.commit()
        
        # 6. Verifikation
        print("\nVerifikation:")
        cursor.execute("SELECT id, title, has_unread_messages_bautraeger, has_unread_messages_dienstleister FROM milestones LIMIT 5")
        results = cursor.fetchall()
        
        for row in results:
            milestone_id, title, bautraeger, dienstleister = row
            print(f"  Milestone {milestone_id} ({title[:30]}...): Bautraeger={bool(bautraeger)}, Dienstleister={bool(dienstleister)}")
        
        print("\nMigration erfolgreich abgeschlossen!")
        return True
        
    except Exception as e:
        print(f"Fehler bei Migration: {e}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = migrate_notification_states()
    sys.exit(0 if success else 1)
