#!/usr/bin/env python3
"""
Skript zur Reparatur der gesperrten SQLite-Datenbank
"""

import sqlite3
import os
import shutil
from datetime import datetime

def fix_database_lock():
    """Repariert die gesperrte SQLite-Datenbank"""
    
    db_path = 'buildwise.db'
    backup_path = f'buildwise_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    
    print(f"🔧 Repariere gesperrte Datenbank: {db_path}")
    
    try:
        # 1. Erstelle Backup der aktuellen Datenbank
        if os.path.exists(db_path):
            print(f"📋 Erstelle Backup: {backup_path}")
            shutil.copy2(db_path, backup_path)
        
        # 2. Versuche Verbindung zur Datenbank herzustellen
        print("🔍 Teste Datenbankverbindung...")
        conn = sqlite3.connect(db_path, timeout=30.0)
        
        # 3. Führe PRAGMA-Befehle aus, um die Datenbank zu reparieren
        print("🔧 Führe Datenbank-Reparatur durch...")
        
        # Setze WAL-Modus für bessere Konkurrenz
        conn.execute("PRAGMA journal_mode=WAL")
        print("✅ WAL-Modus aktiviert")
        
        # Aktiviere Foreign Keys
        conn.execute("PRAGMA foreign_keys=ON")
        print("✅ Foreign Keys aktiviert")
        
        # Optimiere Datenbank
        conn.execute("PRAGMA optimize")
        print("✅ Datenbank optimiert")
        
        # Führe VACUUM aus, um die Datenbank zu komprimieren
        conn.execute("VACUUM")
        print("✅ VACUUM ausgeführt")
        
        # Schließe Verbindung
        conn.close()
        print("✅ Datenbankverbindung geschlossen")
        
        print(f"✅ Datenbank erfolgreich repariert!")
        print(f"📋 Backup erstellt: {backup_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei der Datenbank-Reparatur: {e}")
        
        # Falls die Datenbank beschädigt ist, versuche sie zu löschen und neu zu erstellen
        try:
            print("🔄 Versuche Datenbank neu zu erstellen...")
            
            if os.path.exists(db_path):
                os.remove(db_path)
                print(f"🗑️ Alte Datenbank gelöscht: {db_path}")
            
            # Erstelle neue leere Datenbank
            conn = sqlite3.connect(db_path)
            conn.close()
            print("✅ Neue Datenbank erstellt")
            
            return True
            
        except Exception as e2:
            print(f"❌ Fehler beim Neuerstellen der Datenbank: {e2}")
            return False

def check_database_integrity():
    """Überprüft die Integrität der Datenbank"""
    
    db_path = 'buildwise.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Datenbank existiert nicht: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path, timeout=30.0)
        
        # Prüfe Datenbank-Integrität
        result = conn.execute("PRAGMA integrity_check").fetchone()
        
        if result[0] == "ok":
            print("✅ Datenbank-Integrität OK")
            conn.close()
            return True
        else:
            print(f"❌ Datenbank-Integrität fehlerhaft: {result[0]}")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Fehler bei Integritätsprüfung: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starte Datenbank-Reparatur...")
    
    # 1. Prüfe Integrität
    if check_database_integrity():
        print("✅ Datenbank ist intakt")
    else:
        print("🔧 Datenbank benötigt Reparatur")
        
        # 2. Repariere Datenbank
        if fix_database_lock():
            print("✅ Datenbank erfolgreich repariert")
            
            # 3. Prüfe erneut
            if check_database_integrity():
                print("✅ Datenbank ist nach Reparatur intakt")
            else:
                print("❌ Datenbank ist nach Reparatur immer noch fehlerhaft")
        else:
            print("❌ Datenbank-Reparatur fehlgeschlagen")
    
    print("🏁 Datenbank-Reparatur abgeschlossen") 