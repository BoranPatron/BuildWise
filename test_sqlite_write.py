import sqlite3
import os

db_path = "/var/data/test_db.db"
print(f"🔍 Teste SQLite-Schreibzugriff auf: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT);")
    conn.execute("INSERT INTO test (name) VALUES ('Hallo Render');")
    conn.commit()
    conn.close()
    print("✅ SQLite-Test erfolgreich! Datenbank und Tabelle wurden angelegt und beschrieben.")
    print(f"📄 Datei existiert: {os.path.exists(db_path)} Größe: {os.path.getsize(db_path)} Bytes")
except Exception as e:
    print(f"❌ Fehler beim Schreiben in SQLite-DB: {e}")
    exit(1) 