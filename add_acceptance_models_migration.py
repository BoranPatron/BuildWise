#!/usr/bin/env python3
"""
Migration: Add Acceptance Models
Fügt die neuen Acceptance und AcceptanceDefect Tabellen hinzu
"""

import sqlite3
import sys
from datetime import datetime

def add_acceptance_models():
    """Füge die Acceptance-Tabellen zur Datenbank hinzu"""
    try:
        # Verbinde zur SQLite-Datenbank
        conn = sqlite3.connect('buildwise.db')
        cursor = conn.cursor()
        
        print("🔧 Füge Acceptance-Tabellen hinzu...")
        
        # Erstelle acceptances Tabelle
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS acceptances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            milestone_id INTEGER NOT NULL,
            appointment_id INTEGER,
            contractor_id INTEGER NOT NULL,
            service_provider_id INTEGER NOT NULL,
            created_by INTEGER NOT NULL,
            acceptance_type TEXT NOT NULL DEFAULT 'FINAL',
            status TEXT NOT NULL DEFAULT 'SCHEDULED',
            scheduled_date TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            accepted BOOLEAN,
            acceptance_notes TEXT,
            contractor_notes TEXT,
            service_provider_notes TEXT,
            quality_rating INTEGER,
            timeliness_rating INTEGER,
            overall_rating INTEGER,
            photos TEXT,  -- JSON array
            documents TEXT,  -- JSON array
            protocol_pdf_path TEXT,
            protocol_generated_at TIMESTAMP,
            warranty_start_date TIMESTAMP,
            warranty_period_months INTEGER DEFAULT 24,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (milestone_id) REFERENCES milestones(id) ON DELETE CASCADE,
            FOREIGN KEY (appointment_id) REFERENCES appointments(id),
            FOREIGN KEY (contractor_id) REFERENCES users(id),
            FOREIGN KEY (service_provider_id) REFERENCES users(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
        ''')
        
        # Erstelle acceptance_defects Tabelle
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS acceptance_defects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            acceptance_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            severity TEXT NOT NULL DEFAULT 'MINOR',
            location TEXT,
            room TEXT,
            resolved BOOLEAN DEFAULT FALSE,
            resolution_notes TEXT,
            resolved_at TIMESTAMP,
            resolved_by INTEGER,
            estimated_cost REAL,
            actual_cost REAL,
            deadline TIMESTAMP,
            photos TEXT,  -- JSON array
            resolution_photos TEXT,  -- JSON array
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (acceptance_id) REFERENCES acceptances(id) ON DELETE CASCADE,
            FOREIGN KEY (resolved_by) REFERENCES users(id)
        )
        ''')
        
        # Erstelle Indizes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_acceptances_project ON acceptances(project_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_acceptances_milestone ON acceptances(milestone_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_acceptances_contractor ON acceptances(contractor_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_acceptances_service_provider ON acceptances(service_provider_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_acceptances_status ON acceptances(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_acceptances_created_at ON acceptances(created_at)')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_acceptance_defects_acceptance ON acceptance_defects(acceptance_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_acceptance_defects_resolved ON acceptance_defects(resolved)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_acceptance_defects_severity ON acceptance_defects(severity)')
        
        # Erweitere appointments Tabelle um ACCEPTANCE AppointmentType (falls noch nicht vorhanden)
        try:
            cursor.execute("SELECT appointment_type FROM appointments WHERE appointment_type = 'ACCEPTANCE' LIMIT 1")
        except sqlite3.OperationalError:
            print("📝 AppointmentType ACCEPTANCE ist bereits verfügbar")
        
        # Erweitere document_type um ACCEPTANCE_PROTOCOL (falls noch nicht vorhanden)
        try:
            cursor.execute("SELECT document_type FROM documents WHERE document_type = 'acceptance_protocol' LIMIT 1")
        except sqlite3.OperationalError:
            print("📝 DocumentType acceptance_protocol ist bereits verfügbar")
        
        conn.commit()
        print("✅ Acceptance-Tabellen erfolgreich erstellt")
        
        # Prüfe erstellte Tabellen
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%acceptance%'")
        tables = cursor.fetchall()
        print(f"📊 Gefundene Acceptance-Tabellen: {[table[0] for table in tables]}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Datenbankfehler: {e}")
        return False
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
        return False
    finally:
        if conn:
            conn.close()


def main():
    """Hauptfunktion"""
    print("🚀 Starte Acceptance Models Migration...")
    print(f"📅 Zeitstempel: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    if add_acceptance_models():
        print("=" * 50)
        print("✅ Migration erfolgreich abgeschlossen!")
        sys.exit(0)
    else:
        print("=" * 50)
        print("❌ Migration fehlgeschlagen!")
        sys.exit(1)


if __name__ == "__main__":
    main()