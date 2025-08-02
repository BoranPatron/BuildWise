import sqlite3

# Verbinde zur Datenbank
conn = sqlite3.connect('buildwise.db')
cursor = conn.cursor()

# Prüfe Progress Updates
cursor.execute('SELECT * FROM milestone_progress ORDER BY created_at DESC LIMIT 5')
rows = cursor.fetchall()

print('Letzte 5 Progress Updates:')
if rows:
    for row in rows:
        print(f'  ID: {row[0]}, Milestone: {row[1]}, User: {row[2]}, Type: {row[3]}, Message: {row[4]}')
else:
    print('  Keine Progress Updates gefunden!')

# Prüfe Anzahl
cursor.execute('SELECT COUNT(*) FROM milestone_progress')
count = cursor.fetchone()[0]
print(f'Gesamt: {count} Updates')

conn.close()