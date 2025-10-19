"""
Test-Skript um zu prüfen, ob Benachrichtigungen erstellt werden
"""
import asyncio
import sqlite3
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Check current state
print("=== Aktueller Zustand der Datenbank ===")
conn = sqlite3.connect('buildwise.db')
cursor = conn.cursor()

# Check notifications
cursor.execute('SELECT COUNT(*) FROM notifications')
notif_count = cursor.fetchone()[0]
print(f"Anzahl Benachrichtigungen: {notif_count}")

if notif_count > 0:
    cursor.execute('SELECT id, recipient_id, type, title, is_acknowledged FROM notifications ORDER BY id DESC LIMIT 5')
    results = cursor.fetchall()
    print("\nLetzte Benachrichtigungen:")
    for r in results:
        print(f"  ID={r[0]}, Recipient={r[1]}, Type={r[2]}, Title={r[3]}, Acknowledged={r[4]}")

# Check resource allocations
cursor.execute('SELECT id, resource_id, trade_id, allocation_status FROM resource_allocations ORDER BY id DESC LIMIT 3')
allocs = cursor.fetchall()
print(f"\nLetzte ResourceAllocations:")
for a in allocs:
    print(f"  ID={a[0]}, Resource={a[1]}, Trade={a[2]}, Status={a[3]}")

# Check resources
cursor.execute('SELECT id, service_provider_id, status FROM resources ORDER BY id DESC LIMIT 3')
resources = cursor.fetchall()
print(f"\nLetzte Resources:")
for res in resources:
    print(f"  ID={res[0]}, ServiceProvider={res[1]}, Status={res[2]}")

conn.close()

print("\n=== Test abgeschlossen ===")
print("Erstellen Sie jetzt eine neue Ausschreibung mit einer Ressource und prüfen Sie die Logs.")

