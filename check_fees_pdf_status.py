#!/usr/bin/env python3
"""
Prüfe den PDF-Generierungsstatus der BuildWise-Gebühren
"""

import sqlite3
import os
from datetime import datetime

def check_fees_pdf_status():
    """Prüfe den PDF-Generierungsstatus der BuildWise-Gebühren"""
    
    db_path = 'buildwise.db'
    if not os.path.exists(db_path):
        print(f"❌ Datenbank {db_path} existiert nicht!")
        return
    
    print(f"🔍 Überprüfe PDF-Status in: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Hole alle BuildWise-Gebühren mit PDF-Status
        cursor.execute("""
            SELECT id, project_id, fee_amount, status, 
                   invoice_number, invoice_pdf_generated, invoice_pdf_path,
                   created_at, updated_at
            FROM buildwise_fees
            ORDER BY id
        """)
        
        rows = cursor.fetchall()
        
        print(f"📊 Anzahl BuildWise-Gebühren: {len(rows)}")
        
        if len(rows) == 0:
            print("⚠️ Keine BuildWise-Gebühren gefunden")
            return
        
        print("\n📋 PDF-Status aller Gebühren:")
        print("-" * 80)
        
        for row in rows:
            fee_id, project_id, fee_amount, status, invoice_number, pdf_generated, pdf_path, created_at, updated_at = row
            
            print(f"\n🔍 Gebühr ID {fee_id}:")
            print(f"  Projekt ID: {project_id}")
            print(f"  Betrag: {fee_amount} €")
            print(f"  Status: {status}")
            print(f"  Rechnungsnummer: {invoice_number}")
            print(f"  PDF generiert: {'✅ Ja' if pdf_generated else '❌ Nein'}")
            print(f"  PDF Pfad: {pdf_path or 'Nicht gesetzt'}")
            print(f"  Erstellt: {created_at}")
            print(f"  Aktualisiert: {updated_at}")
            
            # Prüfe ob PDF-Datei existiert
            if pdf_path and os.path.exists(pdf_path):
                print(f"  📄 PDF-Datei existiert: ✅")
            elif pdf_path:
                print(f"  📄 PDF-Datei existiert: ❌ (Pfad: {pdf_path})")
            else:
                print(f"  📄 PDF-Datei existiert: ❌ (Kein Pfad)")
        
        conn.close()
        print("\n✅ PDF-Status-Prüfung abgeschlossen")
        
    except Exception as e:
        print(f"❌ Fehler beim Prüfen des PDF-Status: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_fees_pdf_status() 