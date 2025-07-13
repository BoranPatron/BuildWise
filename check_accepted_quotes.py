import sqlite3

def check_accepted_quotes():
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    # Prüfe alle Angebote
    cursor.execute('SELECT id, title, status, project_id FROM quotes')
    all_quotes = cursor.fetchall()
    print(f"Alle Angebote: {len(all_quotes)}")
    
    # Prüfe akzeptierte Angebote
    cursor.execute('SELECT id, title, status, project_id FROM quotes WHERE LOWER(status) = "accepted"')
    accepted_quotes = cursor.fetchall()
    print(f"Akzeptierte Angebote: {len(accepted_quotes)}")
    
    for quote in accepted_quotes:
        print(f"ID: {quote[0]}, Titel: {quote[1]}, Status: {quote[2]}, Projekt: {quote[3]}")
    
    # Prüfe Kostenpositionen
    cursor.execute('SELECT id, title, quote_id, project_id FROM cost_positions')
    cost_positions = cursor.fetchall()
    print(f"\nKostenpositionen: {len(cost_positions)}")
    
    for cp in cost_positions:
        print(f"ID: {cp[0]}, Titel: {cp[1]}, Quote ID: {cp[2]}, Projekt: {cp[3]}")
    
    conn.close()

if __name__ == "__main__":
    check_accepted_quotes() 