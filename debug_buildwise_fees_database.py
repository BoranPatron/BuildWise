#!/usr/bin/env python3
"""
Debug-Skript für BuildWise-Gebühren Datenbank
Überprüft die buildwise_fees Tabelle und zeigt alle Datensätze an
"""

import sqlite3
import os
from datetime import datetime

def debug_buildwise_fees_database():
    """Überprüft die buildwise_fees Tabelle und zeigt alle Datensätze an"""
    
    # Prüfe ob Datenbank existiert
    db_path = 'buildwise.db'
    if not os.path.exists(db_path):
        print(f"❌ Datenbank {db_path} existiert nicht!")
        return
    
    print(f"🔍 Überprüfe Datenbank: {db_path}")
    
    try:
        # Verbinde zur Datenbank
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Prüfe ob buildwise_fees Tabelle existiert
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='buildwise_fees'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ buildwise_fees Tabelle existiert nicht!")
            return
        
        print("✅ buildwise_fees Tabelle gefunden")
        
        # Hole alle Datensätze
        cursor.execute("SELECT * FROM buildwise_fees")
        rows = cursor.fetchall()
        
        print(f"📊 Anzahl Datensätze in buildwise_fees: {len(rows)}")
        
        if len(rows) == 0:
            print("⚠️ Keine Datensätze in buildwise_fees Tabelle")
            return
        
        # Zeige Spaltennamen
        cursor.execute("PRAGMA table_info(buildwise_fees)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print(f"📋 Spalten: {column_names}")
        
        # Zeige alle Datensätze
        print("\n📋 Alle Datensätze in buildwise_fees:")
        print("-" * 80)
        
        for i, row in enumerate(rows, 1):
            print(f"\n🔍 Datensatz {i}:")
            for j, (col_name, value) in enumerate(zip(column_names, row)):
                # Formatiere Datum-Werte
                if col_name in ['created_at', 'updated_at', 'invoice_date', 'due_date', 'payment_date'] and value:
                    try:
                        # Versuche verschiedene Datumsformate
                        if isinstance(value, str):
                            if 'T' in value:
                                # ISO Format
                                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                formatted_value = dt.strftime('%Y-%m-%d %H:%M:%S')
                            else:
                                # SQLite Format
                                dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                                formatted_value = dt.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            formatted_value = str(value)
                    except:
                        formatted_value = str(value)
                else:
                    formatted_value = str(value)
                
                print(f"  {col_name}: {formatted_value}")
        
        # Prüfe auch buildwise_fee_items Tabelle
        print("\n" + "=" * 80)
        print("🔍 Überprüfe buildwise_fee_items Tabelle")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='buildwise_fee_items'")
        items_table_exists = cursor.fetchone()
        
        if items_table_exists:
            cursor.execute("SELECT COUNT(*) FROM buildwise_fee_items")
            items_count = cursor.fetchone()[0]
            print(f"📊 Anzahl Datensätze in buildwise_fee_items: {items_count}")
            
            if items_count > 0:
                cursor.execute("SELECT * FROM buildwise_fee_items")
                items_rows = cursor.fetchall()
                
                cursor.execute("PRAGMA table_info(buildwise_fee_items)")
                items_columns = cursor.fetchall()
                items_column_names = [col[1] for col in items_columns]
                
                print(f"📋 Spalten: {items_column_names}")
                
                for i, row in enumerate(items_rows, 1):
                    print(f"\n🔍 Fee Item {i}:")
                    for j, (col_name, value) in enumerate(zip(items_column_names, row)):
                        print(f"  {col_name}: {value}")
        else:
            print("❌ buildwise_fee_items Tabelle existiert nicht")
        
        # Teste API-Endpunkt
        print("\n" + "=" * 80)
        print("🔍 Teste API-Endpunkt")
        
        try:
            import requests
            import json
            
            # Teste ohne Token (sollte 401 zurückgeben)
            response = requests.get('http://localhost:8000/api/v1/buildwise-fees/')
            print(f"📡 API Test ohne Token: {response.status_code}")
            
            if response.status_code == 401:
                print("✅ API-Endpunkt erreichbar (401 erwartet ohne Token)")
            else:
                print(f"⚠️ Unerwarteter Status-Code: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"📊 API liefert {len(data)} Datensätze zurück")
                    for i, fee in enumerate(data[:3], 1):  # Zeige nur erste 3
                        print(f"  Fee {i}: ID={fee.get('id')}, Amount={fee.get('fee_amount')}, Status={fee.get('status')}")
            
        except Exception as e:
            print(f"❌ API-Test fehlgeschlagen: {e}")
        
        conn.close()
        print("\n✅ Debug abgeschlossen")
        
    except Exception as e:
        print(f"❌ Fehler beim Debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_buildwise_fees_database() 