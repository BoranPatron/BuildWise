#!/usr/bin/env python3
"""
Migration-Skript für BuildWise PostgreSQL-Datenbank auf Render.com
"""

import os
import sys
from alembic import command
from alembic.config import Config

def run_migrations():
    """Führe alle Migrationen auf der PostgreSQL-Datenbank aus"""
    
    print("🔧 Starte Migrationen für PostgreSQL-Datenbank...")
    
    # Alembic-Konfiguration
    alembic_cfg = Config("alembic.ini")
    
    try:
        # Prüfe Datenbankverbindung
        print("🔍 Prüfe Datenbankverbindung...")
        
        # Führe Migrationen aus
        print("🚀 Führe Migrationen aus...")
        command.upgrade(alembic_cfg, "head")
        
        print("✅ Migrationen erfolgreich ausgeführt!")
        
        # Zeige aktuellen Stand
        print("📊 Aktueller Migrationsstand:")
        command.current(alembic_cfg)
        
    except Exception as e:
        print(f"❌ Fehler bei Migrationen: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migrations() 