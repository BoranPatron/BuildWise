#!/usr/bin/env python3
"""
Einfacher Datenbank-Test
"""

import sqlite3
import os

def test_database():
    """Testet die Datenbank"""
    print("🔍 DATENBANK-TEST")
    print("=" * 30)
    
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
        
        # Teste spezifische Tabellen
        test_tables = ['users', 'projects', 'milestones', 'quotes', 'audit_logs']
        for table in test_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ {table}: {count} Einträge")
            except Exception as e:
                print(f"❌ {table}: Fehler - {e}")
        
        conn.close()
        print("✅ Datenbank-Test erfolgreich!")
        return True
        
    except Exception as e:
        print(f"❌ Datenbank-Fehler: {e}")
        return False

if __name__ == "__main__":
    success = test_database()
    if success:
        print("\n🎉 Datenbank ist bereit!")
    else:
        print("\n💥 Datenbank-Test fehlgeschlagen!") 