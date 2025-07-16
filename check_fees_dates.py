#!/usr/bin/env python3
"""
Prüfe die Datums-Werte der BuildWise-Gebühren
"""

import sqlite3
import os
from datetime import datetime

def check_fees_dates():
    """Prüfe die Datums-Werte der BuildWise-Gebühren"""
    
    db_path = 'buildwise.db'
    if not os.path.exists(db_path):
        print(f"❌ Datenbank {db_path} existiert nicht!")
        return
    
    print(f"🔍 Überprüfe Datums-Werte in: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Hole alle Datensätze mit Datums-Informationen
        cursor.execute("""
            SELECT id, project_id, fee_amount, status, 
                   created_at, updated_at, invoice_date, due_date, payment_date
            FROM buildwise_fees
            ORDER BY id
        """)
        rows = cursor.fetchall()
        
        print(f"📊 Anzahl Datensätze: {len(rows)}")
        
        for row in rows:
            fee_id, project_id, fee_amount, status, created_at, updated_at, invoice_date, due_date, payment_date = row
            
            print(f"\n🔍 Gebühr ID {fee_id}:")
            print(f"  Project: {project_id}")
            print(f"  Amount: {fee_amount}")
            print(f"  Status: {status}")
            print(f"  Created: {created_at}")
            print(f"  Updated: {updated_at}")
            print(f"  Invoice Date: {invoice_date}")
            print(f"  Due Date: {due_date}")
            print(f"  Payment Date: {payment_date}")
            
            # Prüfe ob created_at im Juli 2025 liegt
            if created_at:
                try:
                    created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    print(f"  Created DateTime: {created_dt}")
                    print(f"  Created Month: {created_dt.month}")
                    print(f"  Created Year: {created_dt.year}")
                    print(f"  Im Juli 2025: {created_dt.month == 7 and created_dt.year == 2025}")
                except Exception as e:
                    print(f"  ❌ Fehler beim Parsen von created_at: {e}")
        
        conn.close()
        print("\n✅ Prüfung abgeschlossen")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_fees_dates() 