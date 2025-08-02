import sqlite3

# Verbinde zur Datenbank
conn = sqlite3.connect('buildwise.db')
cursor = conn.cursor()

# Prüfe ob Tabelle existiert
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='milestone_progress'")
table_exists = cursor.fetchone() is not None
print(f'Tabelle milestone_progress existiert: {table_exists}')

if table_exists:
    # Zeige Spalten
    cursor.execute('PRAGMA table_info(milestone_progress)')
    columns = cursor.fetchall()
    print('Spalten:')
    for col in columns:
        print(f'  {col[1]} ({col[2]})')
    
    # Zeige Anzahl Einträge
    cursor.execute('SELECT COUNT(*) FROM milestone_progress')
    count = cursor.fetchone()[0]
    print(f'Anzahl Einträge: {count}')
else:
    print('Tabelle milestone_progress existiert nicht!')

# Prüfe auch service_provider_ratings
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='service_provider_ratings'")
ratings_exists = cursor.fetchone() is not None
print(f'Tabelle service_provider_ratings existiert: {ratings_exists}')

conn.close()