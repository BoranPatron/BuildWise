import sqlite3

print("=== DEBUG: Kostenpositionen und Quotes für Projekt 4 ===\n")

try:
    # Verbinde zur Datenbank
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    print("✅ Datenbankverbindung erfolgreich")
    
    # Prüfe ob die Tabellen existieren
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"📋 Verfügbare Tabellen: {[t[0] for t in tables]}")
    
    print()
    
    # Prüfe Quotes für Projekt 4
    cursor.execute('SELECT id, status, project_id FROM quotes WHERE project_id = 4')
    quotes = cursor.fetchall()
    print(f"Quotes für Projekt 4: {len(quotes)}")
    for quote in quotes:
        print(f"  Quote {quote[0]}: status='{quote[1]}', project_id={quote[2]}")
    
    print()
    
    # Prüfe alle Quotes
    cursor.execute('SELECT id, status, project_id FROM quotes')
    all_quotes = cursor.fetchall()
    print(f"Alle Quotes: {len(all_quotes)}")
    for quote in all_quotes:
        print(f"  Quote {quote[0]}: status='{quote[1]}', project_id={quote[2]}")
    
    print()
    
    # Prüfe Kostenpositionen für Projekt 4
    cursor.execute('SELECT id, quote_id, project_id, cost_type, status FROM cost_positions WHERE project_id = 4')
    cost_positions = cursor.fetchall()
    print(f"Kostenpositionen für Projekt 4: {len(cost_positions)}")
    for cp in cost_positions:
        print(f"  CP {cp[0]}: quote_id={cp[1]}, project_id={cp[2]}, cost_type='{cp[3]}', status='{cp[4]}'")
    
    print()
    
    # Prüfe alle Kostenpositionen
    cursor.execute('SELECT id, quote_id, project_id, cost_type, status FROM cost_positions')
    all_cost_positions = cursor.fetchall()
    print(f"Alle Kostenpositionen: {len(all_cost_positions)}")
    for cp in all_cost_positions:
        print(f"  CP {cp[0]}: quote_id={cp[1]}, project_id={cp[2]}, cost_type='{cp[3]}', status='{cp[4]}'")
    
    print()
    
    # Prüfe alle Quote-Status in der Datenbank
    cursor.execute('SELECT DISTINCT status FROM quotes')
    all_statuses = cursor.fetchall()
    print(f"Alle Quote-Status in der DB: {[s[0] for s in all_statuses]}")
    
    print()
    
    # Prüfe alle CostPosition-Status in der Datenbank
    cursor.execute('SELECT DISTINCT status FROM cost_positions')
    all_cp_statuses = cursor.fetchall()
    print(f"Alle CostPosition-Status in der DB: {[s[0] for s in all_cp_statuses]}")
    
    print()
    
    # Prüfe alle CostPosition-Typen in der Datenbank
    cursor.execute('SELECT DISTINCT cost_type FROM cost_positions')
    all_cp_types = cursor.fetchall()
    print(f"Alle CostPosition-Typen in der DB: {[t[0] for t in all_cp_types]}")
    
    conn.close()
    print("\n✅ Debug abgeschlossen")

except Exception as e:
    print(f"❌ Fehler: {e}")
    import traceback
    traceback.print_exc() 