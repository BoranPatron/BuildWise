import sqlite3

db_path = "buildwise.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Setze die Einwilligungen für den Admin-Benutzer
cur.execute("""
    UPDATE users
    SET data_processing_consent = 1,
        privacy_policy_accepted = 1,
        terms_accepted = 1
    WHERE email = 'admin@buildwise.de'
""")
conn.commit()

print("✅ Einwilligungen für admin@buildwise.de gesetzt!")

# Zeige die Werte zur Kontrolle
for row in cur.execute("SELECT email, data_processing_consent, privacy_policy_accepted, terms_accepted FROM users WHERE email = 'admin@buildwise.de';"):
    print(row)

conn.close()
