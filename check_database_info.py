#!/usr/bin/env python3
"""
Überprüfung der Datenbank-Informationen
"""

import os
import sqlite3

def check_database_info():
    """Überprüft die Datenbank-Informationen"""
    print("🔍 Überprüfe Datenbank-Informationen...")
    
    # Prüfe ob buildwise.db existiert
    if os.path.exists('buildwise.db'):
        print("✅ buildwise.db gefunden")
        
        # Prüfe Dateigröße
        file_size = os.path.getsize('buildwise.db')
        print(f"📊 Dateigröße: {file_size:,} Bytes ({file_size/1024:.1f} KB)")
        
        # Verbinde zur Datenbank
        try:
            conn = sqlite3.connect('buildwise.db')
            cursor = conn.cursor()
            
            # Prüfe Tabellen
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"\n📋 Tabellen in der Datenbank ({len(tables)}):")
            
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  - {table_name}: {count} Einträge")
            
            # Prüfe spezifisch milestones und quotes
            print("\n🔍 Spezielle Überprüfung:")
            
            if 'milestones' in [t[0] for t in tables]:
                cursor.execute("SELECT COUNT(*) FROM milestones")
                milestones_count = cursor.fetchone()[0]
                print(f"  - milestones: {milestones_count} Einträge")
                
                if milestones_count > 0:
                    cursor.execute("SELECT id, title, status FROM milestones LIMIT 3")
                    milestones = cursor.fetchall()
                    for m in milestones:
                        print(f"    * ID {m[0]}: '{m[1]}' (Status: {m[2]})")
            else:
                print("  - milestones: Tabelle nicht gefunden")
            
            if 'quotes' in [t[0] for t in tables]:
                cursor.execute("SELECT COUNT(*) FROM quotes")
                quotes_count = cursor.fetchone()[0]
                print(f"  - quotes: {quotes_count} Einträge")
            else:
                print("  - quotes: Tabelle nicht gefunden")
            
            if 'cost_positions' in [t[0] for t in tables]:
                cursor.execute("SELECT COUNT(*) FROM cost_positions")
                cost_positions_count = cursor.fetchone()[0]
                print(f"  - cost_positions: {cost_positions_count} Einträge")
            else:
                print("  - cost_positions: Tabelle nicht gefunden")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Fehler beim Zugriff auf die Datenbank: {e}")
    
    else:
        print("❌ buildwise.db nicht gefunden!")
    
    # Prüfe Konfiguration
    print("\n⚙️ Datenbank-Konfiguration:")
    print("  - Typ: SQLite (lokale Datei)")
    print("  - Datei: buildwise.db")
    print("  - Engine: sqlite+aiosqlite")
    print("  - Async: Ja")

if __name__ == "__main__":
    check_database_info() 