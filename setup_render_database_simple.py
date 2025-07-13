#!/usr/bin/env python3
"""
Vereinfachtes Setup-Skript für Render.com Datenbank
Verwendet direkt SQLite ohne SQLAlchemy
"""

import sqlite3
import os
import sys

# Füge das Backend-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_render_database_simple():
    """Initialisiert die Datenbank auf Render.com mit direktem SQLite"""
    print("🚀 Starte vereinfachtes Render.com Datenbank-Setup...")
    
    # Datenbank-Pfad
    db_path = "/var/data/buildwise.db"
    print(f"📊 Datenbank-Pfad: {db_path}")
    
    try:
        # Prüfe ob Verzeichnis existiert
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            print(f"❌ Verzeichnis {db_dir} existiert nicht!")
            return False
        
        print(f"✅ Verzeichnis {db_dir} existiert")
        
        # Prüfe Schreibrechte
        if not os.access(db_dir, os.W_OK):
            print(f"❌ Keine Schreibrechte auf {db_dir}!")
            return False
        
        print(f"✅ Schreibrechte auf {db_dir} vorhanden")
        
        # Verbinde zur Datenbank (erstellt sie falls nicht vorhanden)
        print("🔧 Verbinde zur SQLite-Datenbank...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("✅ SQLite-Verbindung erfolgreich")
        
        # Erstelle grundlegende Tabellen
        print("🔧 Erstelle Tabellen...")
        
        # Users-Tabelle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                first_name TEXT,
                last_name TEXT,
                user_type TEXT DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Projects-Tabelle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                project_type TEXT,
                status TEXT DEFAULT 'active',
                budget REAL,
                start_date DATE,
                end_date DATE,
                is_public BOOLEAN DEFAULT 0,
                allow_quotes BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Quotes-Tabelle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                project_id INTEGER,
                service_provider_id INTEGER,
                total_amount REAL,
                currency TEXT DEFAULT 'EUR',
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id),
                FOREIGN KEY (service_provider_id) REFERENCES users (id)
            )
        """)
        
        # Cost Positions-Tabelle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cost_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                amount REAL,
                currency TEXT DEFAULT 'EUR',
                category TEXT,
                status TEXT DEFAULT 'active',
                project_id INTEGER,
                quote_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id),
                FOREIGN KEY (quote_id) REFERENCES quotes (id)
            )
        """)
        
        # Commit Änderungen
        conn.commit()
        print("✅ Tabellen erfolgreich erstellt")
        
        # Prüfe ob bereits Daten vorhanden sind
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count > 0:
            print(f"ℹ️ Datenbank bereits initialisiert ({user_count} Benutzer vorhanden)")
        else:
            print("📝 Datenbank ist leer - Test-Daten können über die API erstellt werden")
        
        # Schließe Verbindung
        conn.close()
        
        print("✅ Datenbank-Setup erfolgreich abgeschlossen!")
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Setup: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = setup_render_database_simple()
    if success:
        print("🎉 Setup erfolgreich!")
    else:
        print("💥 Setup fehlgeschlagen!")
        sys.exit(1) 