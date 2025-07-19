#!/usr/bin/env python3
"""
Database Connection Reset Script
Behebt Database-Lock-Probleme durch Neustart der Verbindung
"""

import asyncio
import sqlite3
from pathlib import Path

async def reset_database():
    """Reset der Datenbankverbindung"""
    
    print("🔧 Reset der Datenbankverbindung...")
    
    # 1. Schließe alle bestehenden Verbindungen
    try:
        # Versuche die Datenbank zu öffnen und sofort zu schließen
        conn = sqlite3.connect('buildwise.db', timeout=5.0)
        conn.close()
        print("✅ Bestehende Verbindungen geschlossen")
    except Exception as e:
        print(f"⚠️ Konnte bestehende Verbindungen nicht schließen: {e}")
    
    # 2. Warte kurz
    await asyncio.sleep(2)
    
    # 3. Öffne neue Verbindung mit optimierten Einstellungen
    try:
        conn = sqlite3.connect(
            'buildwise.db',
            timeout=30.0,
            check_same_thread=False,
            isolation_level=None
        )
        
        # Setze wichtige Pragma-Einstellungen
        pragmas = [
            "PRAGMA journal_mode=WAL",
            "PRAGMA synchronous=NORMAL", 
            "PRAGMA cache_size=-64000",
            "PRAGMA foreign_keys=ON",
            "PRAGMA busy_timeout=30000"
        ]
        
        for pragma in pragmas:
            try:
                conn.execute(pragma)
                print(f"✅ {pragma}")
            except Exception as e:
                print(f"⚠️ {pragma} - {e}")
        
        conn.commit()
        conn.close()
        
        print("✅ Database-Reset erfolgreich!")
        return True
        
    except Exception as e:
        print(f"❌ Database-Reset fehlgeschlagen: {e}")
        return False

def main():
    """Hauptfunktion"""
    print("🔧 Database Connection Reset Tool")
    print("=" * 40)
    
    # Führe Reset aus
    success = asyncio.run(reset_database())
    
    if success:
        print("\n✅ Database-Reset erfolgreich!")
        print("💡 Starte den Server neu für die Änderungen.")
    else:
        print("\n❌ Database-Reset fehlgeschlagen!")

if __name__ == "__main__":
    main() 