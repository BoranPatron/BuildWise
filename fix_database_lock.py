#!/usr/bin/env python3
"""
SQLite Database Lock Fix Script
Behebt Database-Lock-Probleme durch Optimierung der SQLite-Konfiguration
"""

import sqlite3
import os
import asyncio
from pathlib import Path

def fix_sqlite_database():
    """Behebt SQLite Database-Lock-Probleme"""
    
    db_path = Path("buildwise.db")
    
    if not db_path.exists():
        print("❌ Database-Datei nicht gefunden: buildwise.db")
        return False
    
    print("🔧 Behebe SQLite Database-Lock-Probleme...")
    
    try:
        # Verbinde zur Datenbank mit optimierten Einstellungen
        conn = sqlite3.connect(
            str(db_path),
            timeout=30.0,
            check_same_thread=False,
            isolation_level=None  # Autocommit-Modus
        )
        
        # Setze SQLite-Pragma für bessere Performance
        pragma_settings = [
            "PRAGMA journal_mode=WAL;",
            "PRAGMA synchronous=NORMAL;",
            "PRAGMA cache_size=-64000;",
            "PRAGMA temp_store=memory;",
            "PRAGMA mmap_size=268435456;",
            "PRAGMA foreign_keys=ON;",
            "PRAGMA locking_mode=NORMAL;",
            "PRAGMA busy_timeout=30000;",
            "PRAGMA wal_autocheckpoint=1000;",
            "PRAGMA optimize;"
        ]
        
        cursor = conn.cursor()
        
        for pragma in pragma_settings:
            try:
                cursor.execute(pragma)
                print(f"✅ {pragma}")
            except Exception as e:
                print(f"⚠️ {pragma} - {e}")
        
        # Prüfe und repariere die Datenbank
        print("🔍 Prüfe Datenbank-Integrität...")
        cursor.execute("PRAGMA integrity_check;")
        integrity_result = cursor.fetchone()
        
        if integrity_result and integrity_result[0] == "ok":
            print("✅ Datenbank-Integrität OK")
        else:
            print("⚠️ Datenbank-Integrität-Probleme gefunden")
            cursor.execute("PRAGMA quick_check;")
            quick_check = cursor.fetchone()
            print(f"Quick Check: {quick_check}")
        
        # Vakuum die Datenbank (defragmentiert)
        print("🧹 Vakuum der Datenbank...")
        cursor.execute("VACUUM;")
        print("✅ Vakuum abgeschlossen")
        
        # Analysiere die Datenbank
        print("📊 Analysiere Datenbank...")
        cursor.execute("ANALYZE;")
        print("✅ Analyse abgeschlossen")
        
        conn.commit()
        conn.close()
        
        print("🎉 Database-Lock-Fix erfolgreich abgeschlossen!")
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Database-Lock-Fix: {e}")
        return False

def check_database_status():
    """Prüft den aktuellen Status der Datenbank"""
    
    db_path = Path("buildwise.db")
    
    if not db_path.exists():
        print("❌ Database-Datei nicht gefunden")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Prüfe Datenbank-Größe
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size();")
        size_bytes = cursor.fetchone()[0]
        size_mb = size_bytes / (1024 * 1024)
        print(f"📊 Datenbank-Größe: {size_mb:.2f} MB")
        
        # Prüfe Anzahl Tabellen
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📋 Anzahl Tabellen: {len(tables)}")
        
        # Prüfe Journal-Modus
        cursor.execute("PRAGMA journal_mode;")
        journal_mode = cursor.fetchone()[0]
        print(f"📝 Journal-Modus: {journal_mode}")
        
        # Prüfe Locking-Modus
        cursor.execute("PRAGMA locking_mode;")
        locking_mode = cursor.fetchone()[0]
        print(f"🔒 Locking-Modus: {locking_mode}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Fehler beim Prüfen des Database-Status: {e}")

def main():
    """Hauptfunktion"""
    print("🔧 SQLite Database Lock Fix Tool")
    print("=" * 40)
    
    # Prüfe aktuellen Status
    print("\n📊 Aktueller Database-Status:")
    check_database_status()
    
    # Führe Fix aus
    print("\n🔧 Führe Database-Lock-Fix aus...")
    success = fix_sqlite_database()
    
    if success:
        print("\n📊 Neuer Database-Status:")
        check_database_status()
        
        print("\n✅ Database-Lock-Fix erfolgreich!")
        print("💡 Starte den Server neu für die Änderungen.")
    else:
        print("\n❌ Database-Lock-Fix fehlgeschlagen!")

if __name__ == "__main__":
    main() 