#!/usr/bin/env python3
"""
Migration: Gamification-Felder hinzufügen
Fügt die Gamification-Spalten zur users Tabelle hinzu
"""
import sqlite3
import os
import sys
from datetime import datetime

# Windows-Encoding-Fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Datenbank-Pfad
DB_PATH = "buildwise.db"

def check_column_exists(cursor, table_name, column_name):
    """Prüft ob eine Spalte in einer Tabelle existiert"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def add_column_if_not_exists(cursor, table_name, column_name, column_type, default_value=None):
    """Fügt eine Spalte hinzu, falls sie noch nicht existiert"""
    if check_column_exists(cursor, table_name, column_name):
        print(f"  [OK] Spalte '{column_name}' existiert bereits")
        return False
    
    try:
        # SQL für ALTER TABLE mit optionalem DEFAULT
        if default_value is not None:
            if isinstance(default_value, str):
                sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} DEFAULT '{default_value}'"
            else:
                sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} DEFAULT {default_value}"
        else:
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        
        cursor.execute(sql)
        print(f"  [OK] Spalte '{column_name}' erfolgreich hinzugefügt")
        return True
    except sqlite3.Error as e:
        print(f"  [FEHLER] Fehler beim Hinzufügen von '{column_name}': {e}")
        return False

def backup_database(db_path):
    """Erstellt ein Backup der Datenbank"""
    if not os.path.exists(db_path):
        print(f"[WARNUNG] Datenbank '{db_path}' nicht gefunden")
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"[OK] Backup erstellt: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"[FEHLER] Backup fehlgeschlagen: {e}")
        return None

def migrate_gamification_fields(db_path):
    """Führt die Migration für Gamification-Felder durch"""
    print("\n" + "="*60)
    print("MIGRATION: GAMIFICATION-FELDER")
    print("="*60 + "\n")
    
    # Prüfe ob Datenbank existiert
    if not os.path.exists(db_path):
        print(f"[FEHLER] Datenbank '{db_path}' nicht gefunden!")
        return False
    
    print(f"[INFO] Datenbank: {db_path}")
    print(f"[INFO] Größe: {os.path.getsize(db_path) / 1024:.2f} KB\n")
    
    # Erstelle Backup
    print("[INFO] Erstelle Backup...")
    backup_path = backup_database(db_path)
    if not backup_path:
        print("[WARNUNG] Fortfahren ohne Backup? (j/n): ", end="")
        print("j (automatisch)")
    print()
    
    # Verbinde zur Datenbank
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print("[OK] Datenbankverbindung hergestellt\n")
    except sqlite3.Error as e:
        print(f"[FEHLER] Datenbankverbindung fehlgeschlagen: {e}")
        return False
    
    try:
        # Prüfe ob users-Tabelle existiert
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("[FEHLER] Tabelle 'users' nicht gefunden!")
            return False
        
        print("[INFO] Tabelle 'users' gefunden")
        
        # Zeige aktuelle Spalten
        cursor.execute("PRAGMA table_info(users)")
        current_columns = cursor.fetchall()
        print(f"[INFO] Aktuelle Spaltenanzahl: {len(current_columns)}\n")
        
        # Neue Gamification-Spalten
        gamification_columns = [
            ("current_rank_key", "VARCHAR(50)", None),
            ("current_rank_title", "VARCHAR(100)", None),
            ("rank_updated_at", "DATETIME", None)
        ]
        
        # Füge Gamification-Spalten hinzu
        print("[INFO] Füge Gamification-Spalten hinzu:\n")
        added_count = 0
        
        for column_name, column_type, default_value in gamification_columns:
            if add_column_if_not_exists(cursor, "users", column_name, column_type, default_value):
                added_count += 1
        
        # Commit changes
        conn.commit()
        
        # Zeige Ergebnis
        cursor.execute("PRAGMA table_info(users)")
        new_columns = cursor.fetchall()
        
        print("\n" + "-"*60)
        print(f"[OK] Migration abgeschlossen!")
        print(f"  - Spalten vorher: {len(current_columns)}")
        print(f"  - Spalten nachher: {len(new_columns)}")
        print(f"  - Hinzugefügt: {added_count} Gamification-Spalten")
        print("-"*60 + "\n")
        
        # Verifizierung
        print("[INFO] Verifizierung:\n")
        missing_columns = []
        for column_name, _, _ in gamification_columns:
            if check_column_exists(cursor, "users", column_name):
                print(f"  [OK] {column_name}")
            else:
                print(f"  [FEHLT] {column_name} FEHLT!")
                missing_columns.append(column_name)
        
        if missing_columns:
            print(f"\n[FEHLER] Migration unvollständig! Fehlende Spalten: {', '.join(missing_columns)}")
            return False
        
        print("\n[ERFOLG] Alle Gamification-Spalten erfolgreich migriert!")
        
        # Zeige Beispiel-Daten
        print("\n[INFO] Beispiel-Gamification-Daten:")
        cursor.execute("""
            SELECT id, first_name, last_name, completed_offers_count, current_rank_key, current_rank_title
            FROM users 
            WHERE user_role = 'DIENSTLEISTER' 
            LIMIT 3
        """)
        users = cursor.fetchall()
        
        if users:
            for user in users:
                print(f"  - ID: {user[0]}, Name: {user[1]} {user[2]}, Completed: {user[3] or 0}, Rang: {user[4] or 'Nicht gesetzt'}")
        else:
            print("  - Keine Dienstleister gefunden")
        
        return True
        
    except sqlite3.Error as e:
        print(f"\n[FEHLER] Fehler während der Migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
        print("\n[INFO] Datenbankverbindung geschlossen")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  BUILDWISE - GAMIFICATION MIGRATION")
    print("  Fügt Gamification-Spalten hinzu")
    print("="*60)
    
    success = migrate_gamification_fields(DB_PATH)
    
    if success:
        print("\n" + "="*60)
        print("[ERFOLG] MIGRATION ERFOLGREICH ABGESCHLOSSEN")
        print("="*60)
        print("\n[INFO] Die Gamification-Spalten sind jetzt verfügbar.")
        print("   Ränge werden automatisch verwaltet.\n")
    else:
        print("\n" + "="*60)
        print("[FEHLER] MIGRATION FEHLGESCHLAGEN")
        print("="*60)
        print("\n[WARNUNG] Bitte prüfen Sie die Fehlermeldungen oben.")
        print("   Bei Bedarf kann das Backup wiederhergestellt werden.\n")
