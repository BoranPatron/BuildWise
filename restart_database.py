#!/usr/bin/env python3
"""
Einfaches Skript zum Neustart der Datenbank
"""

import os
import sqlite3
import time

def restart_database():
    """Startet die Datenbank neu"""
    
    db_path = 'buildwise.db'
    
    print("🔧 Starte Datenbank neu...")
    
    try:
        # 1. Warte kurz
        time.sleep(2)
        
        # 2. Versuche Verbindung
        print("🔍 Teste Verbindung...")
        conn = sqlite3.connect(db_path, timeout=60.0)
        
        # 3. Führe einfache Reparatur durch
        print("🔧 Repariere Datenbank...")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        
        # 4. Schließe Verbindung
        conn.close()
        
        print("✅ Datenbank erfolgreich neu gestartet!")
        return True
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        
        # 5. Falls fehlgeschlagen, lösche und erstelle neu
        try:
            print("🔄 Erstelle neue Datenbank...")
            if os.path.exists(db_path):
                os.remove(db_path)
            
            conn = sqlite3.connect(db_path)
            conn.close()
            print("✅ Neue Datenbank erstellt")
            return True
            
        except Exception as e2:
            print(f"❌ Fehler beim Neuerstellen: {e2}")
            return False

if __name__ == "__main__":
    restart_database() 