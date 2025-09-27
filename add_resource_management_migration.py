#!/usr/bin/env python3

"""
Migration: Ressourcenverwaltung hinzufügen
Erstellt alle notwendigen Tabellen für die Ressourcenverwaltung.
"""

import sqlite3
import sys
from datetime import datetime

def create_resource_tables(conn):
    """Erstelle alle Resource-Management Tabellen"""
    
    cursor = conn.cursor()
    
    print("🔧 Erstelle Resource-Management Tabellen...")
    
    # 1. Resources Tabelle
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_provider_id INTEGER NOT NULL,
        project_id INTEGER,
        
        -- Zeitraum
        start_date DATETIME NOT NULL,
        end_date DATETIME NOT NULL,
        
        -- Ressourcen-Details
        person_count INTEGER NOT NULL DEFAULT 1,
        daily_hours DECIMAL(5,2) DEFAULT 8.0,
        total_hours DECIMAL(8,2),
        
        -- Kategorie
        category VARCHAR(100) NOT NULL,
        subcategory VARCHAR(100),
        
        -- Adresse
        address_street VARCHAR(255),
        address_city VARCHAR(100),
        address_postal_code VARCHAR(20),
        address_country VARCHAR(100) DEFAULT 'Deutschland',
        latitude DECIMAL(10,8),
        longitude DECIMAL(11,8),
        
        -- Status
        status VARCHAR(20) NOT NULL DEFAULT 'available',
        visibility VARCHAR(20) NOT NULL DEFAULT 'public',
        
        -- Preise
        hourly_rate DECIMAL(10,2),
        daily_rate DECIMAL(10,2),
        currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
        
        -- Zusätzliche Informationen
        description TEXT,
        skills JSON,
        equipment JSON,
        
        -- Computed fields
        provider_name VARCHAR(255),
        provider_email VARCHAR(255),
        active_allocations INTEGER DEFAULT 0,
        
        -- Timestamps
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (service_provider_id) REFERENCES users(id),
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )
    """)
    
    # Indizes für Resources
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_resources_service_provider ON resources(service_provider_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_resources_category ON resources(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_resources_status ON resources(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_resources_start_date ON resources(start_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_resources_end_date ON resources(end_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_resources_city ON resources(address_city)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_resources_location ON resources(latitude, longitude)")
    
    # 2. Resource Allocations Tabelle
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resource_allocations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resource_id INTEGER NOT NULL,
        trade_id INTEGER NOT NULL,
        quote_id INTEGER,
        
        -- Allokations-Details
        allocated_person_count INTEGER NOT NULL,
        allocated_start_date DATETIME NOT NULL,
        allocated_end_date DATETIME NOT NULL,
        allocated_hours DECIMAL(8,2),
        
        -- Status
        allocation_status VARCHAR(20) NOT NULL DEFAULT 'pre_selected',
        
        -- Preise
        agreed_hourly_rate DECIMAL(10,2),
        agreed_daily_rate DECIMAL(10,2),
        total_cost DECIMAL(12,2),
        
        -- Benachrichtigungen
        invitation_sent_at DATETIME,
        invitation_viewed_at DATETIME,
        offer_requested_at DATETIME,
        offer_submitted_at DATETIME,
        decision_made_at DATETIME,
        
        -- Zusätzliche Infos
        notes TEXT,
        rejection_reason TEXT,
        priority INTEGER DEFAULT 5,
        
        -- Timestamps
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        
        FOREIGN KEY (resource_id) REFERENCES resources(id),
        FOREIGN KEY (trade_id) REFERENCES milestones(id),
        FOREIGN KEY (quote_id) REFERENCES quotes(id),
        FOREIGN KEY (created_by) REFERENCES users(id)
    )
    """)
    
    # Indizes für Resource Allocations
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_allocations_resource ON resource_allocations(resource_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_allocations_trade ON resource_allocations(trade_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_allocations_status ON resource_allocations(allocation_status)")
    
    # 3. Resource Requests Tabelle
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resource_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_id INTEGER NOT NULL,
        requested_by INTEGER NOT NULL,
        
        -- Anfrage-Details
        category VARCHAR(100) NOT NULL,
        subcategory VARCHAR(100),
        required_person_count INTEGER NOT NULL,
        required_start_date DATETIME NOT NULL,
        required_end_date DATETIME NOT NULL,
        
        -- Standort
        location_address VARCHAR(500),
        location_city VARCHAR(100),
        location_postal_code VARCHAR(20),
        max_distance_km INTEGER DEFAULT 50,
        
        -- Budget
        max_hourly_rate DECIMAL(10,2),
        max_total_budget DECIMAL(12,2),
        
        -- Anforderungen
        required_skills JSON,
        required_equipment JSON,
        requirements_description TEXT,
        
        -- Status
        status VARCHAR(20) NOT NULL DEFAULT 'open',
        
        -- Statistiken
        total_resources_found INTEGER DEFAULT 0,
        total_resources_selected INTEGER DEFAULT 0,
        total_offers_received INTEGER DEFAULT 0,
        
        -- Timestamps
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        deadline_at DATETIME,
        
        FOREIGN KEY (trade_id) REFERENCES milestones(id),
        FOREIGN KEY (requested_by) REFERENCES users(id)
    )
    """)
    
    # Indizes für Resource Requests
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_trade ON resource_requests(trade_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_category ON resource_requests(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_status ON resource_requests(status)")
    
    # 4. Resource Calendar Entries Tabelle
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resource_calendar_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resource_id INTEGER,
        allocation_id INTEGER,
        service_provider_id INTEGER NOT NULL,
        
        entry_date DATETIME NOT NULL,
        person_count INTEGER NOT NULL DEFAULT 1,
        hours_allocated DECIMAL(5,2),
        
        status VARCHAR(20) NOT NULL DEFAULT 'available',
        
        color VARCHAR(7),
        label VARCHAR(255),
        
        -- Timestamps
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (resource_id) REFERENCES resources(id),
        FOREIGN KEY (allocation_id) REFERENCES resource_allocations(id),
        FOREIGN KEY (service_provider_id) REFERENCES users(id)
    )
    """)
    
    # Indizes für Calendar Entries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_calendar_service_provider ON resource_calendar_entries(service_provider_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_calendar_entry_date ON resource_calendar_entries(entry_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_calendar_status ON resource_calendar_entries(status)")
    
    # 5. Resource KPIs Tabelle
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resource_kpis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_provider_id INTEGER NOT NULL,
        calculation_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        
        total_resources_available INTEGER NOT NULL DEFAULT 0,
        total_resources_allocated INTEGER NOT NULL DEFAULT 0,
        total_resources_completed INTEGER NOT NULL DEFAULT 0,
        
        total_person_days_available INTEGER NOT NULL DEFAULT 0,
        total_person_days_allocated INTEGER NOT NULL DEFAULT 0,
        total_person_days_completed INTEGER NOT NULL DEFAULT 0,
        
        utilization_rate DECIMAL(5,2),
        average_hourly_rate DECIMAL(10,2),
        total_revenue DECIMAL(12,2),
        
        period_start DATETIME NOT NULL,
        period_end DATETIME NOT NULL,
        
        -- Timestamps
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (service_provider_id) REFERENCES users(id)
    )
    """)
    
    # Indizes für KPIs
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_kpis_service_provider ON resource_kpis(service_provider_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_kpis_period ON resource_kpis(period_start, period_end)")
    
    conn.commit()
    print("✅ Resource-Management Tabellen erfolgreich erstellt!")


def check_tables_exist(conn):
    """Prüfe ob die Tabellen bereits existieren"""
    cursor = conn.cursor()
    
    tables_to_check = [
        'resources',
        'resource_allocations', 
        'resource_requests',
        'resource_calendar_entries',
        'resource_kpis'
    ]
    
    existing_tables = []
    for table in tables_to_check:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        )
        if cursor.fetchone():
            existing_tables.append(table)
    
    return existing_tables


def main():
    """Hauptfunktion für die Migration"""
    
    print("🚀 Starte Resource-Management Migration...")
    print(f"📅 Zeitstempel: {datetime.now()}")
    
    # Verbinde zur Datenbank
    try:
        conn = sqlite3.connect('buildwise.db')
        print("✅ Datenbankverbindung hergestellt")
        
        # Prüfe existierende Tabellen
        existing_tables = check_tables_exist(conn)
        if existing_tables:
            print(f"⚠️  Folgende Tabellen existieren bereits: {', '.join(existing_tables)}")
            response = input("Fortfahren? (y/N): ")
            if response.lower() != 'y':
                print("❌ Migration abgebrochen")
                return
        
        # Führe Migration aus
        create_resource_tables(conn)
        
        # Verifiziere Erstellung
        final_tables = check_tables_exist(conn)
        print(f"📋 Erstellte Tabellen: {', '.join(final_tables)}")
        
        # Prüfe Tabellenstrukturen
        cursor = conn.cursor()
        for table in final_tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"📊 {table}: {len(columns)} Spalten")
        
        print("🎉 Resource-Management Migration erfolgreich abgeschlossen!")
        
    except sqlite3.Error as e:
        print(f"❌ Datenbankfehler: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()
            print("🔐 Datenbankverbindung geschlossen")


if __name__ == "__main__":
    main()