#!/usr/bin/env python3
"""
BuildWise Fees Data Ensurer
============================

Stellt sicher, dass die buildwise_fees Tabelle immer gültige Daten enthält
und das Backend nicht abstürzt, wenn die Tabelle leer ist.

Dieses Skript:
1. Prüft ob buildwise_fees Tabelle existiert
2. Prüft ob Daten vorhanden sind
3. Erstellt Standard-Daten falls nötig
4. Validiert die Datenintegrität
"""

import sqlite3
import os
from datetime import datetime, date
import sys

def ensure_buildwise_fees_data():
    """Stellt sicher, dass buildwise_fees Tabelle gültige Daten enthält"""
    
    # Datenbank-Pfad
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Datenbank {db_path} nicht gefunden!")
        return False
    
    print("🔍 Prüfe buildwise_fees Tabelle...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Prüfe ob Tabelle existiert
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='buildwise_fees'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ buildwise_fees Tabelle existiert nicht!")
            print("💡 Führen Sie zuerst die Migration aus: alembic upgrade head")
            return False
        
        print("✅ buildwise_fees Tabelle gefunden")
        
        # 2. Prüfe ob Daten vorhanden sind
        cursor.execute("SELECT COUNT(*) FROM buildwise_fees")
        count = cursor.fetchone()[0]
        
        print(f"📊 Anzahl Datensätze in buildwise_fees: {count}")
        
        if count == 0:
            print("⚠️ Keine Datensätze in buildwise_fees Tabelle - erstelle Standard-Daten...")
            create_default_fees_data(cursor)
        else:
            print("✅ Daten vorhanden - prüfe Datenintegrität...")
            validate_fees_data(cursor)
        
        conn.commit()
        conn.close()
        
        print("✅ buildwise_fees Daten erfolgreich sichergestellt")
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Prüfen der buildwise_fees Daten: {e}")
        return False

def create_default_fees_data(cursor):
    """Erstellt Standard-Daten für buildwise_fees Tabelle"""
    
    print("🔧 Erstelle Standard-Daten für buildwise_fees...")
    
    # Standard-Daten für verschiedene Szenarien
    default_fees = [
        {
            "project_id": 1,
            "quote_id": 1,
            "cost_position_id": 1,
            "service_provider_id": 2,  # Dienstleister
            "fee_amount": 150.00,
            "fee_percentage": 1.0,
            "quote_amount": 15000.00,
            "currency": "EUR",
            "invoice_number": "BW-2024-001",
            "invoice_date": date(2024, 1, 15),
            "due_date": date(2024, 2, 15),
            "status": "open",
            "tax_rate": 19.0,
            "tax_amount": 28.50,
            "net_amount": 150.00,
            "gross_amount": 178.50,
            "fee_details": "Standard BuildWise-Gebühr für erfolgreiche Vermittlung",
            "notes": "Automatisch generiert",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "project_id": 1,
            "quote_id": 2,
            "cost_position_id": 2,
            "service_provider_id": 2,  # Dienstleister
            "fee_amount": 200.00,
            "fee_percentage": 1.0,
            "quote_amount": 20000.00,
            "currency": "EUR",
            "invoice_number": "BW-2024-002",
            "invoice_date": date(2024, 1, 20),
            "due_date": date(2024, 2, 20),
            "status": "open",
            "tax_rate": 19.0,
            "tax_amount": 38.00,
            "net_amount": 200.00,
            "gross_amount": 238.00,
            "fee_details": "BuildWise-Gebühr für Pool-Installation",
            "notes": "Automatisch generiert",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    ]
    
    for fee_data in default_fees:
        try:
            cursor.execute("""
                INSERT INTO buildwise_fees (
                    project_id, quote_id, cost_position_id, service_provider_id,
                    fee_amount, fee_percentage, quote_amount, currency,
                    invoice_number, invoice_date, due_date, status,
                    tax_rate, tax_amount, net_amount, gross_amount,
                    fee_details, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fee_data["project_id"], fee_data["quote_id"], fee_data["cost_position_id"],
                fee_data["service_provider_id"], fee_data["fee_amount"], fee_data["fee_percentage"],
                fee_data["quote_amount"], fee_data["currency"], fee_data["invoice_number"],
                fee_data["invoice_date"], fee_data["due_date"], fee_data["status"],
                fee_data["tax_rate"], fee_data["tax_amount"], fee_data["net_amount"],
                fee_data["gross_amount"], fee_data["fee_details"], fee_data["notes"],
                fee_data["created_at"], fee_data["updated_at"]
            ))
            print(f"✅ Standard-Gebühr erstellt: {fee_data['invoice_number']}")
        except Exception as e:
            print(f"⚠️ Fehler beim Erstellen der Standard-Gebühr {fee_data['invoice_number']}: {e}")
    
    # Prüfe ob Daten erfolgreich erstellt wurden
    cursor.execute("SELECT COUNT(*) FROM buildwise_fees")
    new_count = cursor.fetchone()[0]
    print(f"📊 Neue Anzahl Datensätze in buildwise_fees: {new_count}")

def validate_fees_data(cursor):
    """Validiert die Datenintegrität der buildwise_fees Tabelle"""
    
    print("🔍 Validiere Datenintegrität...")
    
    # Prüfe auf NULL-Werte in wichtigen Feldern
    cursor.execute("""
        SELECT COUNT(*) FROM buildwise_fees 
        WHERE project_id IS NULL OR service_provider_id IS NULL OR fee_amount IS NULL
    """)
    null_count = cursor.fetchone()[0]
    
    if null_count > 0:
        print(f"⚠️ {null_count} Datensätze mit NULL-Werten in wichtigen Feldern gefunden")
    else:
        print("✅ Keine NULL-Werte in wichtigen Feldern")
    
    # Prüfe auf ungültige Beträge
    cursor.execute("""
        SELECT COUNT(*) FROM buildwise_fees 
        WHERE fee_amount <= 0 OR quote_amount <= 0
    """)
    invalid_amount_count = cursor.fetchone()[0]
    
    if invalid_amount_count > 0:
        print(f"⚠️ {invalid_amount_count} Datensätze mit ungültigen Beträgen gefunden")
    else:
        print("✅ Alle Beträge sind gültig")
    
    # Prüfe auf fehlende Rechnungsnummern
    cursor.execute("""
        SELECT COUNT(*) FROM buildwise_fees 
        WHERE invoice_number IS NULL OR invoice_number = ''
    """)
    missing_invoice_count = cursor.fetchone()[0]
    
    if missing_invoice_count > 0:
        print(f"⚠️ {missing_invoice_count} Datensätze ohne Rechnungsnummer gefunden")
    else:
        print("✅ Alle Datensätze haben Rechnungsnummern")
    
    # Zeige Statistiken
    cursor.execute("SELECT COUNT(*), SUM(fee_amount), AVG(fee_amount) FROM buildwise_fees")
    stats = cursor.fetchone()
    print(f"📊 Statistiken: {stats[0]} Gebühren, Gesamt: {stats[1]:.2f}€, Durchschnitt: {stats[2]:.2f}€")

def main():
    """Hauptfunktion"""
    print("🚀 BuildWise Fees Data Ensurer")
    print("=" * 40)
    
    success = ensure_buildwise_fees_data()
    
    if success:
        print("\n✅ BuildWise Fees Daten erfolgreich sichergestellt!")
        print("💡 Das Backend sollte jetzt ohne Fehler starten")
    else:
        print("\n❌ Fehler beim Sichern der BuildWise Fees Daten!")
        print("💡 Prüfen Sie die Datenbank und Migrationen")
        sys.exit(1)

if __name__ == "__main__":
    main() 