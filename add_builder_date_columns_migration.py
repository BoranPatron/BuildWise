#!/usr/bin/env python3
"""
Migration: Add builder preferred date range columns to resources table
Diese Migration fügt Spalten hinzu, um den gewünschten Zeitraum des Bauträgers zu speichern.
"""
import sqlite3
import os
from datetime import datetime

def add_builder_date_columns():
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Datenbank {db_path} nicht gefunden")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Starte Migration: Builder Preferred Date Range Columns")
        print("=" * 60)
        
        # Prüfe ob die Spalten bereits existieren
        cursor.execute("PRAGMA table_info(resources)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        new_columns = [
            ("builder_preferred_start_date", "DATETIME", "Gewünschtes Startdatum des Bauträgers"),
            ("builder_preferred_end_date", "DATETIME", "Gewünschtes Enddatum des Bauträgers"),
            ("builder_date_range_notes", "TEXT", "Notizen zum gewünschten Zeitraum")
        ]
        
        added_columns = []
        
        for column_name, column_type, description in new_columns:
            if column_name not in existing_columns:
                try:
                    alter_sql = f"ALTER TABLE resources ADD COLUMN {column_name} {column_type}"
                    cursor.execute(alter_sql)
                    added_columns.append(column_name)
                    print(f"✅ Spalte '{column_name}' hinzugefügt ({description})")
                except Exception as e:
                    print(f"❌ Fehler beim Hinzufügen der Spalte '{column_name}': {e}")
            else:
                print(f"ℹ️  Spalte '{column_name}' existiert bereits")
        
        # Commit der Änderungen
        conn.commit()
        
        # Prüfe das neue Schema
        print("\n📋 Aktualisiertes Schema der 'resources' Tabelle:")
        print("=" * 60)
        cursor.execute("PRAGMA table_info(resources)")
        columns = cursor.fetchall()
        
        for col in columns:
            cid, name, type_, notnull, dflt_value, pk = col
            if name in [col[0] for col in new_columns]:
                print(f"{cid:2d} | {name:30s} | {type_:15s} | {'NOT NULL' if notnull else 'NULL':8s} | {str(dflt_value) if dflt_value else 'None':10s} | {'PK' if pk else ''} ⭐ NEU")
            else:
                print(f"{cid:2d} | {name:30s} | {type_:15s} | {'NOT NULL' if notnull else 'NULL':8s} | {str(dflt_value) if dflt_value else 'None':10s} | {'PK' if pk else ''}")
        
        conn.close()
        
        if added_columns:
            print(f"\n✅ Migration erfolgreich abgeschlossen!")
            print(f"   {len(added_columns)} neue Spalten hinzugefügt: {', '.join(added_columns)}")
        else:
            print(f"\nℹ️  Keine neuen Spalten hinzugefügt (alle existieren bereits)")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei der Migration: {e}")
        return False

if __name__ == "__main__":
    success = add_builder_date_columns()
    if success:
        print("\n🎉 Migration erfolgreich!")
    else:
        print("\n💥 Migration fehlgeschlagen!")
