#!/usr/bin/env python3
"""
Direkter Backend-Test
"""

import sys
import os

# Füge das aktuelle Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.dirname(__file__))

def test_backend():
    """Testet das Backend direkt"""
    print("🔍 DIREKTER BACKEND-TEST")
    print("=" * 35)
    
    try:
        # Teste Datenbank
        import sqlite3
        db_path = "buildwise.db"
        
        if os.path.exists(db_path):
            print(f"✅ Datenbank gefunden: {os.path.abspath(db_path)}")
            print(f"📊 Größe: {os.path.getsize(db_path)} Bytes")
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Tabellen auflisten
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"📋 Gefundene Tabellen: {len(tables)}")
            
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   - {table_name}: {count} Einträge")
            
            conn.close()
        else:
            print(f"❌ Datenbank nicht gefunden: {db_path}")
        
        # Teste App-Import
        print("\n🔧 Teste App-Import...")
        from app.main import app
        print("✅ App erfolgreich importiert")
        
        # Teste Konfiguration
        from app.core.config import get_settings
        settings = get_settings()
        print(f"✅ Konfiguration geladen: {settings.database_url}")
        
        # Teste Modelle
        from app.models import User, Project, Milestone, Quote, Canvas
        print("✅ Modelle erfolgreich importiert")
        
        print("\n✅ Backend ist bereit!")
        return True
        
    except Exception as e:
        print(f"❌ Backend-Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_backend()
    if success:
        print("\n🎉 Backend-Test erfolgreich!")
    else:
        print("\n💥 Backend-Test fehlgeschlagen!")
        sys.exit(1) 