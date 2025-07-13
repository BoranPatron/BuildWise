import sqlite3

conn = sqlite3.connect('buildwise.db')
cursor = conn.cursor()

# Setze alle Kostenpositionen für Projekt 4 auf die korrekten Enum-Werte
cursor.execute("""
    UPDATE cost_positions
    SET status = 'ACTIVE', cost_type = 'QUOTE_ACCEPTED'
    WHERE project_id = 4
""")
conn.commit()

# Zeige alle Kostenpositionen für Projekt 4 zur Kontrolle
cursor.execute("""
    SELECT id, title, status, cost_type, quote_id, project_id, amount, category
    FROM cost_positions
    WHERE project_id = 4
""")
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()
print("Korrektur abgeschlossen.") 