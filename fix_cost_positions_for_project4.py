import sqlite3
from datetime import datetime

conn = sqlite3.connect('buildwise.db')
cursor = conn.cursor()

# Finde alle akzeptierten Angebote für Projekt 4 ohne Kostenposition
cursor.execute('''
    SELECT q.id, q.title, q.total_amount, q.currency, q.project_id
    FROM quotes q
    LEFT JOIN cost_positions cp ON q.id = cp.quote_id
    WHERE q.project_id = 4 AND q.status = 'accepted' AND cp.id IS NULL
''')
missing = cursor.fetchall()
print(f"Fehlende Kostenpositionen: {len(missing)}")
for quote in missing:
    print(f"  - Angebot ID: {quote[0]}, Titel: {quote[1]}")
    cursor.execute('''
        INSERT INTO cost_positions (
            title, description, amount, currency, category, 
            cost_type, status, project_id, quote_id, 
            contractor_name, progress_percentage, paid_amount,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        f"Kostenposition für {quote[1]}",
        f"Automatisch erstellt aus akzeptiertem Angebot {quote[0]}",
        quote[2],  # amount
        quote[3],  # currency
        "SERVICE",  # category
        "QUOTE_ACCEPTED",  # cost_type
        "ACTIVE",  # status
        quote[4],  # project_id
        quote[0],  # quote_id
        "Auftragnehmer",  # contractor_name
        0,  # progress_percentage
        0,  # paid_amount
        datetime.now().isoformat(),  # created_at
        datetime.now().isoformat()   # updated_at
    ))
    print(f"    ✅ Kostenposition erstellt")
conn.commit()

# Zeige alle Kostenpositionen für Projekt 4 zur Kontrolle
cursor.execute('''
    SELECT cp.id, cp.title, cp.status, cp.cost_type, cp.quote_id, q.status, q.project_id
    FROM cost_positions cp
    LEFT JOIN quotes q ON cp.quote_id = q.id
    WHERE cp.project_id = 4
''')
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()
print("Korrektur abgeschlossen.") 