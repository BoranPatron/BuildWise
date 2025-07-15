import sqlite3
import shutil
import os

DB_PATH = 'buildwise.db'
BACKUP_PATH = 'buildwise_backup_before_all_enum_fix.db'

# Backup anlegen
if not os.path.exists(BACKUP_PATH):
    shutil.copyfile(DB_PATH, BACKUP_PATH)
    print(f"Backup der Datenbank wurde erstellt: {BACKUP_PATH}")
else:
    print(f"Backup existiert bereits: {BACKUP_PATH}")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Liste der Tabellen und Spalten, die Enum-Werte enthalten
enum_fixes = [
    ("projects", "project_type"),
    ("milestones", "status"),
    ("tasks", "status"),
    ("quotes", "status"),
    ("users", "status"),
    ("users", "user_type")
]

for table, column in enum_fixes:
    try:
        # Prüfe, ob die Spalte existiert
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        
        if column not in columns:
            print(f"⚠️ Spalte '{column}' in Tabelle '{table}' nicht gefunden - überspringe")
            continue
            
        # Hole alle unterschiedlichen Werte
        cursor.execute(f"SELECT DISTINCT {column} FROM {table}")
        values = cursor.fetchall()
        
        if not values:
            print(f"ℹ️ Keine Werte in {table}.{column} gefunden")
            continue
            
        print(f"\n🔧 Korrigiere {table}.{column}:")
        print(f"  Vor: {[v[0] for v in values]}")
        
        # Update auf Großbuchstaben
        cursor.execute(f"UPDATE {table} SET {column} = UPPER({column})")
        
        # Kontrolle
        cursor.execute(f"SELECT DISTINCT {column} FROM {table}")
        values_after = cursor.fetchall()
        print(f"  Nach: {[v[0] for v in values_after]}")
        
    except Exception as e:
        print(f"❌ Fehler bei {table}.{column}: {e}")

conn.commit()
conn.close()
print("\n✅ Alle Enum-Werte wurden auf Großbuchstaben gesetzt.") 