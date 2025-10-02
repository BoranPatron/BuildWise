"""
Robuste Migration für User-Schema-Erweiterungen
Fuegt fehlende Spalten fuer Adress- und Steuerinformationen hinzu
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

# Neue Spalten die hinzugefügt werden müssen
NEW_COLUMNS = [
    # Adressfelder
    ("address_street", "VARCHAR", None),
    ("address_zip", "VARCHAR", None),
    ("address_city", "VARCHAR", None),
    ("address_country", "VARCHAR", "Deutschland"),
    ("address_latitude", "FLOAT", None),
    ("address_longitude", "FLOAT", None),
    ("address_geocoded", "BOOLEAN", 0),
    ("address_geocoding_date", "DATETIME", None),
    
    # Steuerfelder
    ("company_tax_number", "VARCHAR(50)", None),
    ("is_small_business", "BOOLEAN", 0),
    ("small_business_exemption", "BOOLEAN", 0),
]


def check_column_exists(cursor, table_name, column_name):
    """Prueft ob eine Spalte in einer Tabelle existiert"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def add_column_if_not_exists(cursor, table_name, column_name, column_type, default_value):
    """Fuegt eine Spalte hinzu, falls sie noch nicht existiert"""
    if check_column_exists(cursor, table_name, column_name):
        print(f"  [OK] Spalte '{column_name}' existiert bereits")
        return False
    
    try:
        # SQL fuer ALTER TABLE mit optionalem DEFAULT
        if default_value is not None:
            if isinstance(default_value, str):
                sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} DEFAULT '{default_value}'"
            else:
                sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} DEFAULT {default_value}"
        else:
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        
        cursor.execute(sql)
        print(f"  [OK] Spalte '{column_name}' erfolgreich hinzugefuegt")
        return True
    except sqlite3.Error as e:
        print(f"  [FEHLER] Fehler beim Hinzufuegen von '{column_name}': {e}")
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


def migrate_user_schema(db_path):
    """Fuehrt die Schema-Migration durch"""
    print("\n" + "="*60)
    print("USER-SCHEMA MIGRATION")
    print("="*60 + "\n")
    
    # Prüfe ob Datenbank existiert
    if not os.path.exists(db_path):
        print(f"[FEHLER] Datenbank '{db_path}' nicht gefunden!")
        return False
    
    print(f"[INFO] Datenbank: {db_path}")
    print(f"[INFO] Groesse: {os.path.getsize(db_path) / 1024:.2f} KB\n")
    
    # Erstelle Backup
    print("[INFO] Erstelle Backup...")
    backup_path = backup_database(db_path)
    if not backup_path:
        print("[WARNUNG] Fortfahren ohne Backup? (j/n): ", end="")
        # Automatisch fortfahren fuer Skript-Ausfuehrung
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
        # Pruefe ob users-Tabelle existiert
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("[FEHLER] Tabelle 'users' nicht gefunden!")
            return False
        
        print("[INFO] Tabelle 'users' gefunden")
        
        # Zeige aktuelle Spalten
        cursor.execute("PRAGMA table_info(users)")
        current_columns = cursor.fetchall()
        print(f"[INFO] Aktuelle Spaltenanzahl: {len(current_columns)}\n")
        
        # Fuege neue Spalten hinzu
        print("[INFO] Fuege neue Spalten hinzu:\n")
        added_count = 0
        failed_count = 0
        
        for column_name, column_type, default_value in NEW_COLUMNS:
            if add_column_if_not_exists(cursor, "users", column_name, column_type, default_value):
                added_count += 1
            else:
                if not check_column_exists(cursor, "users", column_name):
                    failed_count += 1
        
        # Commit changes
        conn.commit()
        
        # Zeige Ergebnis
        cursor.execute("PRAGMA table_info(users)")
        new_columns = cursor.fetchall()
        
        print("\n" + "-"*60)
        print(f"[OK] Migration abgeschlossen!")
        print(f"  - Spalten vorher: {len(current_columns)}")
        print(f"  - Spalten nachher: {len(new_columns)}")
        print(f"  - Hinzugefuegt: {added_count}")
        print(f"  - Bereits vorhanden: {len(NEW_COLUMNS) - added_count - failed_count}")
        if failed_count > 0:
            print(f"  - Fehlgeschlagen: {failed_count}")
        print("-"*60 + "\n")
        
        # Verifizierung
        print("[INFO] Verifizierung:\n")
        missing_columns = []
        for column_name, _, _ in NEW_COLUMNS:
            if check_column_exists(cursor, "users", column_name):
                print(f"  [OK] {column_name}")
            else:
                print(f"  [FEHLT] {column_name} FEHLT!")
                missing_columns.append(column_name)
        
        if missing_columns:
            print(f"\n[FEHLER] Migration unvollstaendig! Fehlende Spalten: {', '.join(missing_columns)}")
            return False
        
        print("\n[ERFOLG] Alle Spalten erfolgreich migriert!")
        return True
        
    except sqlite3.Error as e:
        print(f"\n[FEHLER] Fehler waehrend der Migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
        print("\n[INFO] Datenbankverbindung geschlossen")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  BUILDWISE - USER SCHEMA MIGRATION")
    print("  Adress- und Steuerfelder")
    print("="*60)
    
    success = migrate_user_schema(DB_PATH)
    
    if success:
        print("\n" + "="*60)
        print("[ERFOLG] MIGRATION ERFOLGREICH ABGESCHLOSSEN")
        print("="*60)
        print("\n[INFO] Die Anwendung kann jetzt neu gestartet werden.")
        print("   Social-Login sollte nun funktionieren.\n")
    else:
        print("\n" + "="*60)
        print("[FEHLER] MIGRATION FEHLGESCHLAGEN")
        print("="*60)
        print("\n[WARNUNG] Bitte pruefen Sie die Fehlermeldungen oben.")
        print("   Bei Bedarf kann das Backup wiederhergestellt werden.\n")

