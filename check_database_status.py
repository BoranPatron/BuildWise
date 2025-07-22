#!/usr/bin/env python3
"""
Überprüft den Status der Datenbank
"""

import os
import sqlite3

def check_database_status():
    """Überprüft den Datenbank-Status"""
    print("🔍 DATENBANK-STATUS ÜBERPRÜFUNG")
    print("=" * 40)
    
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Datenbank nicht gefunden: {db_path}")
        return False
    
    print(f"✅ Datenbank gefunden: {os.path.abspath(db_path)}")
    print(f"📊 Größe: {os.path.getsize(db_path)} Bytes")
    
    try:
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
        print("✅ Datenbank-Status OK")
        return True
        
    except Exception as e:
        print(f"❌ Datenbank-Fehler: {e}")
        return False

if __name__ == "__main__":
    check_database_status() 