import sqlite3

db_path = "buildwise.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Zeige alle Status-Werte vor der Korrektur
print("Vorher:")
for row in cur.execute("SELECT id, email, status FROM users;"):
    print(row)

# Korrigiere die Status-Werte auf Großbuchstaben
cur.execute("UPDATE users SET status = 'ACTIVE' WHERE status = 'active';")
cur.execute("UPDATE users SET status = 'INACTIVE' WHERE status = 'inactive';")
cur.execute("UPDATE users SET status = 'SUSPENDED' WHERE status = 'suspended';")
cur.execute("UPDATE users SET status = 'DELETED' WHERE status = 'deleted';")
conn.commit()

print("\nNachher:")
for row in cur.execute("SELECT id, email, status FROM users;"):
    print(row)

conn.close()
print("\n✅ Status-Felder erfolgreich korrigiert!")