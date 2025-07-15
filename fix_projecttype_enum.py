import sqlite3
import shutil
import os

DB_PATH = 'buildwise.db'
BACKUP_PATH = 'buildwise_backup_before_enum_fix.db'

# Backup anlegen
if not os.path.exists(BACKUP_PATH):
    shutil.copyfile(DB_PATH, BACKUP_PATH)
    print(f"Backup der Datenbank wurde erstellt: {BACKUP_PATH}")
else:
    print(f"Backup existiert bereits: {BACKUP_PATH}")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Prüfe, ob die Spalte existiert
cursor.execute("PRAGMA table_info(projects)")
columns = [col[1] for col in cursor.fetchall()]
if 'project_type' not in columns:
    print("Spalte 'project_type' nicht gefunden!")
    conn.close()
    exit(1)

# Hole alle unterschiedlichen Werte
cursor.execute("SELECT DISTINCT project_type FROM projects")
values = cursor.fetchall()
print("Gefundene Werte vor Änderung:", [v[0] for v in values])

# Update auf Großbuchstaben
cursor.execute("UPDATE projects SET project_type = UPPER(project_type)")
conn.commit()

# Kontrolle
cursor.execute("SELECT DISTINCT project_type FROM projects")
values_after = cursor.fetchall()
print("Werte nach Änderung:", [v[0] for v in values_after])

conn.close()
print("Fertig. Alle project_type-Werte wurden auf Großbuchstaben gesetzt.") 