"""
Datenbank-Migration: Stripe Payment Integration für BuildWise Fees
Fuegt notwendige Spalten fuer Stripe Payment Links hinzu
"""

import sqlite3
import sys
from pathlib import Path

def add_stripe_columns():
    """Fuegt Stripe-Spalten zur buildwise_fees Tabelle hinzu"""
    
    db_path = Path("buildwise.db")
    
    if not db_path.exists():
        print("[ERROR] buildwise.db nicht gefunden")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("[INFO] Starte Migration: Stripe Payment Columns")
        
        # Pruefe ob Spalten bereits existieren
        cursor.execute("PRAGMA table_info(buildwise_fees)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        columns_to_add = {
            'stripe_payment_link_id': 'VARCHAR(255)',
            'stripe_payment_link_url': 'VARCHAR(500)',
            'stripe_payment_intent_id': 'VARCHAR(255)',
            'stripe_checkout_session_id': 'VARCHAR(255)',
            'payment_method': 'VARCHAR(50)'
        }
        
        added_count = 0
        for column_name, column_type in columns_to_add.items():
            if column_name not in existing_columns:
                print(f"  [+] Fuege Spalte hinzu: {column_name}")
                cursor.execute(f"ALTER TABLE buildwise_fees ADD COLUMN {column_name} {column_type}")
                added_count += 1
            else:
                print(f"  [OK] Spalte existiert bereits: {column_name}")
        
        # Erstelle Indizes fuer Performance
        indexes = [
            ('idx_stripe_payment_link_id', 'stripe_payment_link_id'),
            ('idx_stripe_payment_intent_id', 'stripe_payment_intent_id'),
            ('idx_stripe_checkout_session_id', 'stripe_checkout_session_id')
        ]
        
        for index_name, column_name in indexes:
            try:
                print(f"  [INDEX] Erstelle Index: {index_name}")
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON buildwise_fees({column_name})")
            except sqlite3.OperationalError as e:
                if "already exists" not in str(e):
                    print(f"  [WARNING] Index {index_name} konnte nicht erstellt werden: {e}")
        
        conn.commit()
        
        print(f"\n[SUCCESS] Migration erfolgreich abgeschlossen!")
        print(f"   - {added_count} neue Spalten hinzugefuegt")
        print(f"   - {len(indexes)} Indizes erstellt")
        
        # Zeige Tabellenstruktur
        cursor.execute("PRAGMA table_info(buildwise_fees)")
        columns = cursor.fetchall()
        print(f"\n[INFO] Aktuelle Tabellenstruktur (buildwise_fees):")
        print(f"   Anzahl Spalten: {len(columns)}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Fehler bei der Migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("Stripe Payment Integration - Datenbank-Migration")
    print("=" * 70)
    print()
    
    success = add_stripe_columns()
    
    if success:
        print("\n[SUCCESS] Migration erfolgreich!")
        print("   Die Datenbank ist jetzt bereit fuer Stripe-Zahlungen.")
        sys.exit(0)
    else:
        print("\n[ERROR] Migration fehlgeschlagen!")
        print("   Bitte pruefen Sie die Fehlermeldungen.")
        sys.exit(1)

