#!/usr/bin/env python3
"""
Migration: Create appointment_responses table
Erstellt eine separate Tabelle für Terminantworten anstatt JSON in appointments.responses
"""

import sqlite3
import json
from datetime import datetime
import os

def create_appointment_responses_table():
    """Erstelle die neue appointment_responses Tabelle"""
    
    # Verbindung zur Datenbank
    db_path = "buildwise.db"
    if not os.path.exists(db_path):
        print(f"❌ Datenbank {db_path} nicht gefunden!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Neue Tabelle erstellen
        print("📋 Erstelle appointment_responses Tabelle...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointment_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_id INTEGER NOT NULL,
                service_provider_id INTEGER NOT NULL,
                status VARCHAR(50) NOT NULL CHECK (status IN ('accepted', 'rejected', 'rejected_with_suggestion')),
                message TEXT,
                suggested_date DATETIME,
                responded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE,
                FOREIGN KEY (service_provider_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(appointment_id, service_provider_id)
            )
        """)
        
        # 2. Indizes erstellen
        print("🔍 Erstelle Indizes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_appointment_responses_appointment 
            ON appointment_responses(appointment_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_appointment_responses_provider 
            ON appointment_responses(service_provider_id)
        """)
        
        # 3. Bestehende JSON-Daten migrieren
        print("📦 Migriere bestehende responses...")
        cursor.execute("SELECT id, responses FROM appointments WHERE responses IS NOT NULL AND responses != ''")
        appointments = cursor.fetchall()
        
        migrated_count = 0
        for appointment_id, responses_json in appointments:
            try:
                if responses_json:
                    # JSON parsen
                    if isinstance(responses_json, str):
                        responses = json.loads(responses_json)
                    else:
                        responses = responses_json
                    
                    if isinstance(responses, list):
                        for response in responses:
                            if isinstance(response, dict) and 'service_provider_id' in response:
                                # Response in neue Tabelle einfügen
                                cursor.execute("""
                                    INSERT OR REPLACE INTO appointment_responses 
                                    (appointment_id, service_provider_id, status, message, suggested_date, responded_at)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """, (
                                    appointment_id,
                                    response.get('service_provider_id'),
                                    response.get('status', 'accepted'),
                                    response.get('message'),
                                    response.get('suggested_date'),
                                    response.get('responded_at', datetime.utcnow().isoformat())
                                ))
                                migrated_count += 1
                                
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"⚠️ Fehler beim Migrieren von Appointment {appointment_id}: {e}")
                continue
        
        conn.commit()
        print(f"✅ Migration erfolgreich! {migrated_count} Antworten migriert.")
        
        # 4. Überprüfung
        cursor.execute("SELECT COUNT(*) FROM appointment_responses")
        count = cursor.fetchone()[0]
        print(f"📊 Gesamt {count} Antworten in neuer Tabelle")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei Migration: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def verify_migration():
    """Überprüfe die Migration"""
    conn = sqlite3.connect("buildwise.db")
    cursor = conn.cursor()
    
    try:
        # Tabelle existiert?
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='appointment_responses'")
        if not cursor.fetchone():
            print("❌ Tabelle appointment_responses existiert nicht!")
            return False
        
        # Daten vorhanden?
        cursor.execute("SELECT COUNT(*) FROM appointment_responses")
        count = cursor.fetchone()[0]
        print(f"✅ Tabelle appointment_responses enthält {count} Einträge")
        
        # Beispiel-Daten anzeigen
        cursor.execute("""
            SELECT ar.appointment_id, ar.service_provider_id, ar.status, ar.responded_at,
                   u.first_name, u.last_name, u.company_name
            FROM appointment_responses ar
            LEFT JOIN users u ON ar.service_provider_id = u.id
            LIMIT 5
        """)
        
        print("\n📋 Beispiel-Daten:")
        for row in cursor.fetchall():
            print(f"  Termin {row[0]}: {row[4]} {row[5]} ({row[6]}) - {row[2]} - {row[3]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei Überprüfung: {e}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Starte Migration zu appointment_responses Tabelle...")
    
    if create_appointment_responses_table():
        print("\n🔍 Überprüfe Migration...")
        verify_migration()
        print("\n✅ Migration abgeschlossen!")
    else:
        print("\n❌ Migration fehlgeschlagen!") 