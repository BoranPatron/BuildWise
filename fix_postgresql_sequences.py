#!/usr/bin/env python3
"""
PostgreSQL Sequences zurücksetzen für BuildWise
Behebt Auto-Increment Konflikte nach der Migration
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# Konfiguration
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "buildwise",
    "user": "buildwise_user",
    "password": "buildwise123"
}

def connect_postgresql():
    """Verbindung zur PostgreSQL-Datenbank herstellen"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Fehler beim Verbinden zur PostgreSQL-Datenbank: {e}")
        return None

def get_table_info(conn):
    """Informationen über alle Tabellen abrufen"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Alle Tabellen mit ihren Sequences abrufen
    cursor.execute("""
        SELECT 
            t.table_name,
            c.column_name,
            c.column_default,
            c.is_nullable,
            c.data_type
        FROM information_schema.tables t
        JOIN information_schema.columns c ON t.table_name = c.table_name
        WHERE t.table_schema = 'public' 
        AND t.table_type = 'BASE TABLE'
        AND c.column_name = 'id'
        ORDER BY t.table_name
    """)
    
    return cursor.fetchall()

def get_max_id(conn, table_name):
    """Maximale ID einer Tabelle abrufen"""
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT MAX(id) FROM {table_name}")
        result = cursor.fetchone()
        return result[0] if result[0] is not None else 0
    except Exception as e:
        print(f"   ⚠️  Fehler beim Abrufen der max ID für {table_name}: {e}")
        return 0

def reset_sequence(conn, table_name, max_id):
    """Sequence für eine Tabelle zurücksetzen"""
    cursor = conn.cursor()
    sequence_name = f"{table_name}_id_seq"
    
    try:
        # Sequence zurücksetzen
        next_value = max_id + 1
        cursor.execute(f"SELECT setval('{sequence_name}', {next_value}, false)")
        print(f"   ✅ Sequence {sequence_name} auf {next_value} gesetzt")
        return True
    except Exception as e:
        print(f"   ❌ Fehler beim Zurücksetzen der Sequence {sequence_name}: {e}")
        return False

def main():
    """Hauptfunktion für das Zurücksetzen der Sequences"""
    print("🔧 Starte PostgreSQL Sequences Reset")
    print("=" * 50)
    
    # Verbindung herstellen
    conn = connect_postgresql()
    if not conn:
        return False
    
    try:
        # Tabelleninformationen abrufen
        tables = get_table_info(conn)
        print(f"📋 Gefundene Tabellen mit ID-Spalten: {len(tables)}")
        
        successful_resets = []
        failed_resets = []
        
        for table_info in tables:
            table_name = table_info['table_name']
            print(f"\n🔄 Verarbeite Tabelle: {table_name}")
            
            # Maximale ID abrufen
            max_id = get_max_id(conn, table_name)
            print(f"   📊 Maximale ID: {max_id}")
            
            # Sequence zurücksetzen
            if reset_sequence(conn, table_name, max_id):
                successful_resets.append(table_name)
            else:
                failed_resets.append(table_name)
        
        # Änderungen committen
        conn.commit()
        
        # Zusammenfassung
        print(f"\n📊 SEQUENCE RESET ZUSAMMENFASSUNG")
        print("=" * 50)
        print(f"✅ Erfolgreich zurückgesetzt: {len(successful_resets)} Tabellen")
        print(f"❌ Fehlgeschlagen: {len(failed_resets)} Tabellen")
        
        if successful_resets:
            print(f"\n✅ Erfolgreiche Resets:")
            for table in successful_resets:
                print(f"   - {table}")
        
        if failed_resets:
            print(f"\n❌ Fehlgeschlagene Resets:")
            for table in failed_resets:
                print(f"   - {table}")
        
        return len(failed_resets) == 0
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Sequence Reset erfolgreich abgeschlossen!")
    else:
        print("\n⚠️  Sequence Reset mit Fehlern abgeschlossen.") 