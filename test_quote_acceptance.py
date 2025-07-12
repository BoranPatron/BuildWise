#!/usr/bin/env python3
"""
Test-Skript für das Akzeptieren von Angeboten und die Erstellung von Kostenpositionen
"""

import sys
import os
import asyncio
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def test_quote_acceptance():
    """Testet das Akzeptieren von Angeboten und die Erstellung von Kostenpositionen"""
    print("🧪 Test: Angebot akzeptieren und Kostenposition erstellen")
    print("=" * 60)
    
    # Direkte SQLite-Verbindung für Tests
    DATABASE_URL = "sqlite:///buildwise.db"
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # 1. Prüfe aktuelle Angebote
        print("\n📋 Aktuelle Angebote:")
        result = conn.execute(text("SELECT id, title, status, project_id FROM quotes"))
        quotes = result.fetchall()
        
        if not quotes:
            print("❌ Keine Angebote in der Datenbank gefunden")
            return
        
        for quote in quotes:
            print(f"  - ID: {quote[0]}, Titel: {quote[1]}, Status: {quote[2]}, Projekt: {quote[3]}")
        
        # 2. Prüfe aktuelle Kostenpositionen
        print("\n💰 Aktuelle Kostenpositionen:")
        result = conn.execute(text("SELECT id, title, quote_id, project_id FROM cost_positions"))
        cost_positions = result.fetchall()
        
        if not cost_positions:
            print("❌ Keine Kostenpositionen in der Datenbank gefunden")
        else:
            for cp in cost_positions:
                print(f"  - ID: {cp[0]}, Titel: {cp[1]}, Quote-ID: {cp[2]}, Projekt: {cp[3]}")
        
        # 3. Teste das Akzeptieren eines Angebots
        print("\n🔧 Test: Angebot akzeptieren...")
        
        # Finde ein Angebot mit Status 'submitted'
        result = conn.execute(text("SELECT id, title FROM quotes WHERE status = 'submitted' LIMIT 1"))
        quote_to_accept = result.fetchone()
        
        if not quote_to_accept:
            print("❌ Kein Angebot mit Status 'submitted' gefunden")
            print("💡 Tipp: Erstelle zuerst ein Angebot und setze es auf 'submitted'")
            return
        
        quote_id = quote_to_accept[0]
        quote_title = quote_to_accept[1]
        
        print(f"✅ Teste Akzeptieren von Angebot: {quote_title} (ID: {quote_id})")
        
        # Simuliere das Akzeptieren (Status auf 'accepted' setzen)
        conn.execute(
            text("UPDATE quotes SET status = 'accepted', accepted_at = :now WHERE id = :quote_id"),
            {"now": datetime.utcnow().isoformat(), "quote_id": quote_id}
        )
        conn.commit()
        
        print(f"✅ Angebot {quote_id} auf 'accepted' gesetzt")
        
        # 4. Prüfe, ob eine Kostenposition erstellt wurde
        print("\n🔍 Prüfe Kostenposition...")
        result = conn.execute(text("SELECT id, title FROM cost_positions WHERE quote_id = :quote_id"), 
                            {"quote_id": quote_id})
        cost_position = result.fetchone()
        
        if cost_position:
            print(f"✅ Kostenposition gefunden: {cost_position[1]} (ID: {cost_position[0]})")
        else:
            print("❌ Keine Kostenposition für das akzeptierte Angebot gefunden")
            print("💡 Das Backend sollte automatisch eine Kostenposition erstellen")
        
        # 5. Prüfe den aktuellen Status
        print("\n📊 Aktueller Status:")
        result = conn.execute(text("SELECT id, title, status FROM quotes WHERE id = :quote_id"), 
                            {"quote_id": quote_id})
        quote_status = result.fetchone()
        if quote_status:
            print(f"  - Angebot: {quote_status[1]} (Status: {quote_status[2]})")
        else:
            print("  - Angebot: Nicht gefunden")
        
        if cost_position:
            print(f"  - Kostenposition: {cost_position[1]} (erstellt)")
        else:
            print("  - Kostenposition: NICHT ERSTELLT")
        
        print("\n" + "=" * 60)
        print("🎯 Test abgeschlossen")

if __name__ == "__main__":
    test_quote_acceptance() 