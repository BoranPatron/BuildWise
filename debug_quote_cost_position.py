#!/usr/bin/env python3
"""
Debug-Skript für Angebot-Kostenposition-Verbindung
Prüft, ob für ein akzeptiertes Angebot eine Kostenposition existiert
"""

import sqlite3
import requests
import json
from datetime import datetime

def debug_quote_cost_position_connection(quote_id: int | None = None):
    """Debuggt die Verbindung zwischen Angebot und Kostenposition"""
    
    print("🔍 Debug: Angebot-Kostenposition-Verbindung")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('buildwise.db')
        cursor = conn.cursor()
        
        # 1. Prüfe alle akzeptierten Angebote
        print("\n1️⃣ Akzeptierte Angebote:")
        cursor.execute("""
            SELECT id, title, project_id, status, total_amount, currency, accepted_at
            FROM quotes 
            WHERE status = 'ACCEPTED'
            ORDER BY id
        """)
        accepted_quotes = cursor.fetchall()
        
        if not accepted_quotes:
            print("❌ Keine akzeptierten Angebote gefunden")
            return
        
        print(f"📊 Gefundene akzeptierte Angebote: {len(accepted_quotes)}")
        
        for quote in accepted_quotes:
            quote_id, title, project_id, status, amount, currency, accepted_at = quote
            print(f"   - ID: {quote_id}, Titel: '{title}', Projekt: {project_id}, Betrag: {amount} {currency}")
        
        # 2. Prüfe alle Kostenpositionen
        print("\n2️⃣ Kostenpositionen:")
        cursor.execute("""
            SELECT id, title, project_id, quote_id, amount, currency, cost_type, status
            FROM cost_positions 
            ORDER BY id
        """)
        cost_positions = cursor.fetchall()
        
        if not cost_positions:
            print("❌ Keine Kostenpositionen gefunden")
        else:
            print(f"📊 Gefundene Kostenpositionen: {len(cost_positions)}")
            
            for cp in cost_positions:
                cp_id, title, project_id, quote_id, amount, currency, cost_type, status = cp
                print(f"   - ID: {cp_id}, Titel: '{title}', Projekt: {project_id}, Quote-ID: {quote_id}, Betrag: {amount} {currency}, Typ: {cost_type}, Status: {status}")
        
        # 3. Prüfe spezifisches Angebot (falls angegeben)
        if quote_id:
            print(f"\n3️⃣ Spezifische Prüfung für Angebot ID {quote_id}:")
            
            # Prüfe Angebot
            cursor.execute("""
                SELECT id, title, project_id, status, total_amount, currency, accepted_at
                FROM quotes 
                WHERE id = ?
            """, (quote_id,))
            quote = cursor.fetchone()
            
            if not quote:
                print(f"❌ Angebot ID {quote_id} nicht gefunden")
                return
            
            q_id, title, project_id, status, amount, currency, accepted_at = quote
            print(f"   📋 Angebot: '{title}' (Projekt {project_id}, Status: {status}, Betrag: {amount} {currency})")
            
            # Prüfe zugehörige Kostenposition
            cursor.execute("""
                SELECT id, title, project_id, quote_id, amount, currency, cost_type, status
                FROM cost_positions 
                WHERE quote_id = ?
            """, (quote_id,))
            cost_position = cursor.fetchone()
            
            if cost_position:
                cp_id, cp_title, cp_project_id, cp_quote_id, cp_amount, cp_currency, cp_cost_type, cp_status = cost_position
                print(f"   ✅ Kostenposition gefunden: ID {cp_id}, '{cp_title}' (Betrag: {cp_amount} {cp_currency})")
                
                # Prüfe Konsistenz
                if cp_amount != amount:
                    print(f"   ⚠️ Warnung: Betrag stimmt nicht überein (Angebot: {amount}, Kostenposition: {cp_amount})")
                if cp_project_id != project_id:
                    print(f"   ⚠️ Warnung: Projekt stimmt nicht überein (Angebot: {project_id}, Kostenposition: {cp_project_id})")
                if cp_currency != currency:
                    print(f"   ⚠️ Warnung: Währung stimmt nicht überein (Angebot: {currency}, Kostenposition: {cp_currency})")
            else:
                print(f"   ❌ Keine Kostenposition für Angebot ID {quote_id} gefunden")
                
                # Erstelle Kostenposition manuell
                print(f"   🔧 Erstelle Kostenposition für Angebot ID {quote_id}...")
                create_cost_position_for_quote(cursor, quote_id, title, project_id, amount, currency)
        
        # 4. Prüfe alle Angebote ohne Kostenposition
        print("\n4️⃣ Angebote ohne Kostenposition:")
        cursor.execute("""
            SELECT q.id, q.title, q.project_id, q.status, q.total_amount, q.currency
            FROM quotes q
            LEFT JOIN cost_positions cp ON q.id = cp.quote_id
            WHERE q.status = 'ACCEPTED' AND cp.id IS NULL
            ORDER BY q.id
        """)
        quotes_without_cp = cursor.fetchall()
        
        if quotes_without_cp:
            print(f"📊 Gefundene Angebote ohne Kostenposition: {len(quotes_without_cp)}")
            for quote in quotes_without_cp:
                q_id, title, project_id, status, amount, currency = quote
                print(f"   - ID: {q_id}, Titel: '{title}', Projekt: {project_id}, Betrag: {amount} {currency}")
                
                # Erstelle Kostenposition
                print(f"   🔧 Erstelle Kostenposition für Angebot ID {q_id}...")
                create_cost_position_for_quote(cursor, q_id, title, project_id, amount, currency)
        else:
            print("✅ Alle akzeptierten Angebote haben eine Kostenposition")
        
        # 5. Teste API
        print("\n5️⃣ API-Test:")
        test_api_cost_positions()
        
        conn.commit()
        conn.close()
        
        print("\n✅ Debug abgeschlossen")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        if 'conn' in locals():
            conn.close()

def create_cost_position_for_quote(cursor, quote_id: int, title: str, project_id: int, amount: float, currency: str):
    """Erstellt eine Kostenposition für ein Angebot"""
    try:
        # Bestimme Kategorie basierend auf Titel
        title_lower = title.lower()
        category = 'OTHER'
        
        if any(keyword in title_lower for keyword in ['elektro', 'elektrik', 'strom']):
            category = 'ELECTRICAL'
        elif any(keyword in title_lower for keyword in ['sanitär', 'wasser', 'rohr']):
            category = 'PLUMBING'
        elif any(keyword in title_lower for keyword in ['heizung', 'wärme']):
            category = 'HEATING'
        elif any(keyword in title_lower for keyword in ['dach', 'ziegel']):
            category = 'ROOFING'
        elif any(keyword in title_lower for keyword in ['mauer', 'stein']):
            category = 'MASONRY'
        elif any(keyword in title_lower for keyword in ['trockenbau', 'gips']):
            category = 'DRYWALL'
        elif any(keyword in title_lower for keyword in ['maler', 'farbe']):
            category = 'PAINTING'
        elif any(keyword in title_lower for keyword in ['boden', 'fliese']):
            category = 'FLOORING'
        elif any(keyword in title_lower for keyword in ['garten', 'landschaft']):
            category = 'LANDSCAPING'
        elif any(keyword in title_lower for keyword in ['küche']):
            category = 'KITCHEN'
        elif any(keyword in title_lower for keyword in ['bad', 'badezimmer']):
            category = 'BATHROOM'
        
        # Erstelle Kostenposition
        cursor.execute("""
            INSERT INTO cost_positions (
                project_id, title, description, amount, currency, category, 
                cost_type, status, quote_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            f"Kostenposition: {title}",
            f"Kostenposition für {title}",
            amount,
            currency,
            category,
            'QUOTE_ACCEPTED',
            'ACTIVE',
            quote_id,
            datetime.utcnow(),
            datetime.utcnow()
        ))
        
        cost_position_id = cursor.lastrowid
        print(f"   ✅ Kostenposition erstellt: ID {cost_position_id}")
        
    except Exception as e:
        print(f"   ❌ Fehler beim Erstellen der Kostenposition: {e}")

def test_api_cost_positions():
    """Testet die API für Kostenpositionen"""
    try:
        # Login
        login_data = {
            'username': 'admin@buildwise.de',
            'password': 'admin123'
        }
        
        response = requests.post(
            'http://localhost:8000/api/v1/auth/login',
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        if response.status_code != 200:
            print("❌ Login fehlgeschlagen")
            return
        
        data = response.json()
        token = data['access_token']
        print("✅ Login erfolgreich")
        
        # Teste Kostenpositionen für Projekt 4
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(
            'http://localhost:8000/api/v1/cost-positions/?project_id=4&accepted_quotes_only=true',
            headers=headers
        )
        
        print(f"📡 API Status: {response.status_code}")
        
        if response.status_code == 200:
            cost_positions = response.json()
            print(f"✅ API: {len(cost_positions)} Kostenpositionen gefunden")
            
            for cp in cost_positions:
                print(f"   - {cp['title']}: {cp['amount']} {cp['currency']}")
        else:
            print(f"❌ API-Fehler: {response.text}")
            
    except Exception as e:
        print(f"❌ API-Test Fehler: {e}")

if __name__ == "__main__":
    import sys
    
    # Prüfe Kommandozeilen-Argumente
    quote_id = None
    if len(sys.argv) > 1:
        try:
            quote_id = int(sys.argv[1])
            print(f"🔍 Debug für spezifisches Angebot ID: {quote_id}")
        except ValueError:
            print("❌ Ungültige Angebots-ID. Verwende alle Angebote.")
    
    debug_quote_cost_position_connection(quote_id) 