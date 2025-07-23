#!/usr/bin/env python3
"""
SQLite zu PostgreSQL Datenmigration für BuildWise
Migriert alle Daten unter Berücksichtigung der Datentyp-Kompatibilität
"""

import sqlite3
import psycopg2
import json
from datetime import datetime
from decimal import Decimal
import os
from typing import Any, Dict, List, Tuple

# Konfiguration
SQLITE_DB_PATH = "buildwise.db"  # Pfad zur SQLite-Datenbank
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "buildwise",
    "user": "buildwise_user",
    "password": "buildwise123"
}

def connect_sqlite():
    """Verbindung zur SQLite-Datenbank herstellen"""
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"❌ SQLite-Datenbank nicht gefunden: {SQLITE_DB_PATH}")
        return None
    
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row  # Ermöglicht Spaltenzugriff über Namen
        return conn
    except Exception as e:
        print(f"❌ Fehler beim Verbinden zur SQLite-Datenbank: {e}")
        return None

def connect_postgresql():
    """Verbindung zur PostgreSQL-Datenbank herstellen"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Fehler beim Verbinden zur PostgreSQL-Datenbank: {e}")
        return None

def get_table_names(sqlite_conn):
    """Alle Tabellennamen aus SQLite abrufen"""
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    return [row[0] for row in cursor.fetchall()]

def get_table_schema(sqlite_conn, table_name):
    """Tabellenschema aus SQLite abrufen"""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return cursor.fetchall()

def convert_datetime(value):
    """SQLite datetime zu PostgreSQL timestamp konvertieren"""
    if value is None:
        return None
    if isinstance(value, str):
        # SQLite datetime Format: 'YYYY-MM-DD HH:MM:SS'
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except:
            return value
    return value

def convert_decimal(value):
    """Wert zu Decimal konvertieren für numerische Felder"""
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except:
        return value

def convert_json(value):
    """JSON-String zu PostgreSQL JSON konvertieren"""
    if value is None:
        return None
    if isinstance(value, str):
        try:
            # Validiere JSON
            json.loads(value)
            return value
        except:
            return value
    return value

def convert_value(value, column_type):
    """Wert basierend auf Spaltentyp konvertieren"""
    if value is None:
        return None
    
    # PostgreSQL-spezifische Typkonvertierung
    if 'timestamp' in column_type.lower() or 'datetime' in column_type.lower():
        return convert_datetime(value)
    elif 'numeric' in column_type.lower() or 'decimal' in column_type.lower():
        return convert_decimal(value)
    elif 'json' in column_type.lower():
        return convert_json(value)
    elif 'boolean' in column_type.lower():
        return bool(value) if value is not None else None
    else:
        return value

def migrate_table(sqlite_conn, postgres_conn, table_name):
    """Einzelne Tabelle migrieren"""
    print(f"🔄 Migriere Tabelle: {table_name}")
    
    # Schema abrufen
    schema = get_table_schema(sqlite_conn, table_name)
    columns = [col[1] for col in schema]  # Spaltennamen
    types = [col[2] for col in schema]    # Spaltentypen
    
    # Daten aus SQLite abrufen
    cursor = sqlite_conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    if not rows:
        print(f"   ⚠️  Tabelle {table_name} ist leer")
        return True
    
    print(f"   📊 {len(rows)} Zeilen gefunden")
    
    # Daten in PostgreSQL einfügen
    postgres_cursor = postgres_conn.cursor()
    
    # Platzhalter für INSERT-Statement erstellen
    placeholders = ', '.join(['%s'] * len(columns))
    column_list = ', '.join(columns)
    
    success_count = 0
    error_count = 0
    
    for row in rows:
        try:
            # Werte konvertieren
            converted_values = []
            for i, value in enumerate(row):
                converted_value = convert_value(value, types[i])
                converted_values.append(converted_value)
            
            # INSERT-Statement ausführen
            insert_sql = f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})"
            postgres_cursor.execute(insert_sql, converted_values)
            success_count += 1
            
        except Exception as e:
            error_count += 1
            print(f"   ❌ Fehler bei Zeile {success_count + error_count}: {e}")
            print(f"      Werte: {converted_values}")
            continue
    
    postgres_conn.commit()
    print(f"   ✅ {success_count} Zeilen erfolgreich migriert")
    if error_count > 0:
        print(f"   ❌ {error_count} Zeilen mit Fehlern")
    
    return error_count == 0

def check_data_integrity(sqlite_conn, postgres_conn, table_name):
    """Datenintegrität zwischen SQLite und PostgreSQL prüfen"""
    print(f"🔍 Prüfe Datenintegrität für Tabelle: {table_name}")
    
    # Zeilenanzahl vergleichen
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    sqlite_count = sqlite_cursor.fetchone()[0]
    
    postgres_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    postgres_count = postgres_cursor.fetchone()[0]
    
    print(f"   📊 SQLite: {sqlite_count} Zeilen, PostgreSQL: {postgres_count} Zeilen")
    
    if sqlite_count == postgres_count:
        print(f"   ✅ Zeilenanzahl stimmt überein")
        return True
    else:
        print(f"   ❌ Zeilenanzahl stimmt nicht überein!")
        return False

def main():
    """Hauptfunktion für die Datenmigration"""
    print("🚀 Starte SQLite zu PostgreSQL Datenmigration")
    print("=" * 50)
    
    # Verbindungen herstellen
    sqlite_conn = connect_sqlite()
    if not sqlite_conn:
        return False
    
    postgres_conn = connect_postgresql()
    if not postgres_conn:
        sqlite_conn.close()
        return False
    
    try:
        # Tabellen abrufen
        tables = get_table_names(sqlite_conn)
        print(f"📋 Gefundene Tabellen: {', '.join(tables)}")
        print()
        
        # Migration durchführen
        successful_tables = []
        failed_tables = []
        
        for table_name in tables:
            try:
                success = migrate_table(sqlite_conn, postgres_conn, table_name)
                if success:
                    successful_tables.append(table_name)
                else:
                    failed_tables.append(table_name)
                print()
            except Exception as e:
                print(f"❌ Fehler bei Migration von Tabelle {table_name}: {e}")
                failed_tables.append(table_name)
                print()
        
        # Datenintegrität prüfen
        print("🔍 Prüfe Datenintegrität...")
        print("=" * 50)
        
        integrity_checks = []
        for table_name in successful_tables:
            integrity_ok = check_data_integrity(sqlite_conn, postgres_conn, table_name)
            integrity_checks.append((table_name, integrity_ok))
            print()
        
        # Zusammenfassung
        print("📊 MIGRATION ZUSAMMENFASSUNG")
        print("=" * 50)
        print(f"✅ Erfolgreich migriert: {len(successful_tables)} Tabellen")
        print(f"❌ Fehlgeschlagen: {len(failed_tables)} Tabellen")
        
        if successful_tables:
            print(f"\n✅ Erfolgreiche Tabellen:")
            for table in successful_tables:
                print(f"   - {table}")
        
        if failed_tables:
            print(f"\n❌ Fehlgeschlagene Tabellen:")
            for table in failed_tables:
                print(f"   - {table}")
        
        print(f"\n🔍 Datenintegrität:")
        for table_name, integrity_ok in integrity_checks:
            status = "✅ OK" if integrity_ok else "❌ FEHLER"
            print(f"   - {table_name}: {status}")
        
        return len(failed_tables) == 0
        
    finally:
        sqlite_conn.close()
        postgres_conn.close()

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Migration erfolgreich abgeschlossen!")
    else:
        print("\n⚠️  Migration mit Fehlern abgeschlossen. Bitte prüfen Sie die Logs.") 