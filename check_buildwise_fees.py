#!/usr/bin/env python3
"""
Skript zur Überprüfung der BuildWise-Gebühren in der Datenbank
"""

import sqlite3

def check_buildwise_fees():
    """Überprüfe BuildWise-Gebühren in der Datenbank"""
    try:
        conn = sqlite3.connect('buildwise.db')
        cursor = conn.cursor()
        
        # Prüfe ob Tabelle existiert
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='buildwise_fees'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ buildwise_fees Tabelle existiert nicht!")
            return
        
        # Hole alle Gebühren
        cursor.execute("SELECT * FROM buildwise_fees")
        fees = cursor.fetchall()
        
        print(f"📊 Gefundene BuildWise-Gebühren: {len(fees)}")
        
        if len(fees) > 0:
            print("\n📋 Gebühren-Details:")
            for fee in fees:
                print(f"  - ID: {fee[0]}, User: {fee[1]}, Projekt: {fee[2]}")
                print(f"    Monat: {fee[3]}/{fee[4]}, Betrag: {fee[5]}€, Status: {fee[10]}")
                print()
        else:
            print("⚠️ Keine Gebühren in der Datenbank gefunden")
        
        # Prüfe auch buildwise_fee_items
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='buildwise_fee_items'")
        items_table_exists = cursor.fetchone()
        
        if items_table_exists:
            cursor.execute("SELECT * FROM buildwise_fee_items")
            items = cursor.fetchall()
            print(f"📊 Gefundene Gebühren-Items: {len(items)}")
            
            if len(items) > 0:
                print("\n📋 Items-Details:")
                for item in items:
                    print(f"  - ID: {item[0]}, Gebühr-ID: {item[1]}, Angebot-ID: {item[2]}")
                    print(f"    Angebot-Betrag: {item[4]}€, Gebühren-Betrag: {item[5]}€")
                    print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Fehler beim Überprüfen der Gebühren: {e}")

if __name__ == "__main__":
    check_buildwise_fees() 