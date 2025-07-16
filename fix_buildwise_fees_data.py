#!/usr/bin/env python3
"""
Skript zur Korrektur der BuildWise-Fees-Daten
"""

import sqlite3
from datetime import datetime

def fix_buildwise_fees_data():
    """Korrigiert die BuildWise-Fees-Daten in der Datenbank"""
    
    try:
        # Verbinde zur Datenbank
        conn = sqlite3.connect('buildwise.db')
        cursor = conn.cursor()
        
        print("🔧 Korrigiere BuildWise-Fees-Daten...")
        
        # Aktualisiere buildwise_fees Tabelle
        cursor.execute("""
            UPDATE buildwise_fees 
            SET created_at = datetime('now'), updated_at = datetime('now') 
            WHERE created_at IS NULL OR updated_at IS NULL
        """)
        
        fees_updated = cursor.rowcount
        print(f"✅ {fees_updated} BuildWise-Fees aktualisiert")
        
        # Aktualisiere buildwise_fee_items Tabelle
        cursor.execute("""
            UPDATE buildwise_fee_items 
            SET created_at = datetime('now') 
            WHERE created_at IS NULL
        """)
        
        items_updated = cursor.rowcount
        print(f"✅ {items_updated} BuildWise-Fee-Items aktualisiert")
        
        # Commit Änderungen
        conn.commit()
        
        # Prüfe die Daten
        cursor.execute("SELECT COUNT(*) FROM buildwise_fees")
        total_fees = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM buildwise_fees WHERE created_at IS NOT NULL")
        fees_with_timestamp = cursor.fetchone()[0]
        
        print(f"📊 Gesamt: {total_fees} Gebühren, {fees_with_timestamp} mit Timestamp")
        
        if total_fees == fees_with_timestamp:
            print("✅ Alle BuildWise-Fees haben korrekte Timestamps")
        else:
            print("⚠️ Einige BuildWise-Fees haben noch keine Timestamps")
        
        conn.close()
        print("✅ Datenbank-Verbindung geschlossen")
        
    except Exception as e:
        print(f"❌ Fehler beim Korrigieren der Daten: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_buildwise_fees_data() 