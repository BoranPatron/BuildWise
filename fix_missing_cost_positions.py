#!/usr/bin/env python3
"""
Skript zur Reparatur fehlender Kostenpositionen für akzeptierte Angebote.
"""

import sqlite3
import os
from datetime import datetime

def fix_missing_cost_positions():
    """Erstellt fehlende Kostenpositionen für akzeptierte Angebote"""
    
    db_path = "buildwise.db"
    if not os.path.exists(db_path):
        print(f"❌ Datenbank {db_path} nicht gefunden!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Suche nach akzeptierten Angeboten ohne Kostenposition...")
    
    # Hole alle akzeptierten Angebote
    cursor.execute("SELECT id, title, project_id, milestone_id, total_amount, currency FROM quotes WHERE status = 'accepted'")
    accepted_quotes = cursor.fetchall()
    
    print(f"📊 Gefundene akzeptierte Angebote: {len(accepted_quotes)}")
    
    # Prüfe für jedes Angebot, ob eine Kostenposition existiert
    missing_cost_positions = []
    for quote in accepted_quotes:
        quote_id, title, project_id, milestone_id, total_amount, currency = quote
        
        # Prüfe, ob bereits eine Kostenposition für dieses Quote existiert
        cursor.execute("SELECT id FROM cost_positions WHERE quote_id = ?", (quote_id,))
        existing_cost_position = cursor.fetchone()
        
        if not existing_cost_position:
            missing_cost_positions.append(quote)
            print(f"⚠️  Quote {quote_id} ({title}) hat keine Kostenposition")
        else:
            print(f"✅ Quote {quote_id} ({title}) hat bereits Kostenposition {existing_cost_position[0]}")
    
    print(f"\n📋 Fehlende Kostenpositionen: {len(missing_cost_positions)}")
    
    # Erstelle fehlende Kostenpositionen
    created_count = 0
    for quote in missing_cost_positions:
        try:
            quote_id, title, project_id, milestone_id, total_amount, currency = quote
            print(f"🔧 Erstelle Kostenposition für Quote {quote_id} ({title})...")
            
            # Bestimme Kategorie basierend auf Milestone-Titel
            category = 'other'
            if milestone_id:
                cursor.execute("SELECT title FROM milestones WHERE id = ?", (milestone_id,))
                milestone_result = cursor.fetchone()
                if milestone_result:
                    milestone_title = milestone_result[0].lower()
                    if 'elektro' in milestone_title:
                        category = 'electrical'
                    elif 'sanitär' in milestone_title:
                        category = 'plumbing'
                    elif 'heizung' in milestone_title:
                        category = 'heating'
                    elif 'dach' in milestone_title:
                        category = 'roofing'
                    elif 'mauerwerk' in milestone_title:
                        category = 'masonry'
                    elif 'trockenbau' in milestone_title:
                        category = 'drywall'
                    elif 'maler' in milestone_title:
                        category = 'painting'
                    elif 'boden' in milestone_title:
                        category = 'flooring'
                    elif 'garten' in milestone_title:
                        category = 'landscaping'
                    elif 'küche' in milestone_title:
                        category = 'kitchen'
                    elif 'bad' in milestone_title:
                        category = 'bathroom'
            
            # Erstelle Kostenposition
            cursor.execute("""
                INSERT INTO cost_positions (
                    project_id, title, description, amount, currency, category, 
                    cost_type, status, quote_id, milestone_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project_id,
                f"Kostenposition: {title}",
                f"Kostenposition für {title}",
                total_amount,
                currency or 'EUR',
                category,
                'quote_accepted',
                'active',
                quote_id,
                milestone_id,
                datetime.now(),
                datetime.now()
            ))
            
            created_count += 1
            print(f"✅ Kostenposition für Quote {quote_id} erfolgreich erstellt")
            
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der Kostenposition für Quote {quote_id}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n🎉 Reparatur abgeschlossen!")
    print(f"  • Akzeptierte Angebote: {len(accepted_quotes)}")
    print(f"  • Fehlende Kostenpositionen: {len(missing_cost_positions)}")
    print(f"  • Erfolgreich erstellt: {created_count}")
    
    # Finale Validierung
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM quotes WHERE status = 'accepted'")
    total_accepted = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM quotes q 
        LEFT JOIN cost_positions cp ON q.id = cp.quote_id 
        WHERE q.status = 'accepted' AND cp.id IS NULL
    """)
    final_missing = cursor.fetchone()[0]
    
    conn.close()
    
    if final_missing == 0:
        print("✅ Alle akzeptierten Angebote haben jetzt eine Kostenposition!")
    else:
        print(f"⚠️  {final_missing} Angebote haben immer noch keine Kostenposition")

if __name__ == "__main__":
    fix_missing_cost_positions() 