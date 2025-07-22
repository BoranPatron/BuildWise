import sqlite3
import os

def check_database():
    """Überprüft die Datenbankstruktur und den Inhalt"""
    
    if not os.path.exists('buildwise.db'):
        print("❌ Datenbank buildwise.db nicht gefunden!")
        return
    
    print("✅ Datenbank buildwise.db gefunden")
    
    try:
        conn = sqlite3.connect('buildwise.db')
        cursor = conn.cursor()
        
        # Alle Tabellen auflisten
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n📋 Verfügbare Tabellen ({len(tables)}):")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Spezifische Tabellen überprüfen
        important_tables = ['cost_positions', 'quotes', 'projects', 'users', 'milestones']
        
        print(f"\n🔍 Überprüfung wichtiger Tabellen:")
        for table in important_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} Einträge")
            
            if count > 0:
                # Erste paar Einträge anzeigen
                cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                rows = cursor.fetchall()
                print(f"    Erste Einträge:")
                for row in rows:
                    print(f"      {row}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Fehler beim Überprüfen der Datenbank: {e}")

if __name__ == "__main__":
    check_database() 