#!/usr/bin/env python3
"""
Überprüft, ob die Datenbank wirklich leer ist
"""

import sqlite3
import os

def check_database_empty():
    """Überprüft den tatsächlichen Inhalt der Datenbank"""
    print("🔍 DATENBANK-LEERHEIT PRÜFUNG")
    print("=" * 40)
    
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Datenbank nicht gefunden: {db_path}")
        return
    
    print(f"📁 Datenbank: {os.path.abspath(db_path)}")
    print(f"📊 Größe: {os.path.getsize(db_path)} Bytes")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Tabellen auflisten
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\n📋 Gefundene Tabellen: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Jede Tabelle prüfen
        total_records = 0
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            total_records += count
            
            if count > 0:
                print(f"\n📊 {table_name}: {count} Einträge")
                
                # Erste 3 Einträge zeigen
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                records = cursor.fetchall()
                
                # Spaltennamen holen
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cursor.fetchall()]
                
                for i, record in enumerate(records, 1):
                    print(f"   {i}. {dict(zip(columns, record))}")
            else:
                print(f"\n📊 {table_name}: 0 Einträge (LEER)")
        
        print(f"\n📈 GESAMT: {total_records} Einträge in der Datenbank")
        
        if total_records == 0:
            print("❌ DATENBANK IST WIRKLICH LEER!")
        else:
            print("✅ Datenbank enthält Daten")
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_database_empty() 