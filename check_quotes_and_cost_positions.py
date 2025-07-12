import sqlite3

DB_PATH = "buildwise.db"  # Passe den Pfad ggf. an

def print_table(title, rows, columns):
    print(f"\n--- {title} ---")
    if not rows:
        print("Keine Einträge gefunden.")
        return
    print(" | ".join(columns))
    print("-" * (len(columns) * 18))
    for row in rows:
        print(" | ".join(str(row[col]) for col in columns))

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Akzeptierte Angebote anzeigen
    cur.execute("SELECT id, title, status, project_id FROM quotes WHERE status = 'accepted'")
    accepted_quotes = cur.fetchall()
    print_table("Akzeptierte Angebote (quotes)", accepted_quotes, ["id", "title", "status", "project_id"])

    # 2. Kostenpositionen mit quote_id anzeigen
    cur.execute("SELECT id, title, amount, quote_id, project_id FROM cost_positions WHERE quote_id IS NOT NULL")
    cost_positions = cur.fetchall()
    print_table("Kostenpositionen mit quote_id (cost_positions)", cost_positions, ["id", "title", "amount", "quote_id", "project_id"])

    # 3. Kostenpositionen ohne quote_id anzeigen (optional)
    cur.execute("SELECT id, title, amount, quote_id, project_id FROM cost_positions WHERE quote_id IS NULL")
    cost_positions_no_quote = cur.fetchall()
    print_table("Kostenpositionen ohne quote_id (optional)", cost_positions_no_quote, ["id", "title", "amount", "quote_id", "project_id"])

    conn.close()

if __name__ == "__main__":
    main() 