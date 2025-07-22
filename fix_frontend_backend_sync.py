#!/usr/bin/env python3
"""
Synchronisation von Frontend und Backend
"""

import sqlite3
import os
import requests
import json

def check_frontend_backend_sync():
    """Überprüft die Synchronisation zwischen Frontend und Backend"""
    print("🔍 Überprüfe Frontend-Backend-Synchronisation...")
    
    # 1. Datenbank-Status prüfen
    print("\n📊 DATENBANK-STATUS:")
    print("=" * 30)
    
    if not os.path.exists('buildwise.db'):
        print("❌ buildwise.db nicht gefunden!")
        return
    
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    try:
        # Milestones prüfen
        cursor.execute("SELECT COUNT(*) FROM milestones")
        milestones_count = cursor.fetchone()[0]
        print(f"📋 Milestones in DB: {milestones_count}")
        
        # Quotes prüfen
        cursor.execute("SELECT COUNT(*) FROM quotes")
        quotes_count = cursor.fetchone()[0]
        print(f"💰 Quotes in DB: {quotes_count}")
        
        # Cost Positions prüfen
        cursor.execute("SELECT COUNT(*) FROM cost_positions")
        cost_positions_count = cursor.fetchone()[0]
        print(f"💼 Cost Positions in DB: {cost_positions_count}")
        
    except Exception as e:
        print(f"❌ Fehler beim Datenbank-Zugriff: {e}")
        return
    finally:
        conn.close()
    
    # 2. Backend-API prüfen
    print("\n🌐 BACKEND-API-STATUS:")
    print("=" * 30)
    
    try:
        # Teste Backend-Verfügbarkeit
        response = requests.get('http://localhost:8000/docs', timeout=5)
        print(f"✅ Backend erreichbar: {response.status_code}")
        
        # Teste Milestones-API
        response = requests.get('http://localhost:8000/api/v1/milestones', timeout=5)
        print(f"📋 Milestones API: {response.status_code}")
        if response.status_code == 200:
            milestones_data = response.json()
            print(f"   Milestones vom Backend: {len(milestones_data)}")
        
        # Teste Quotes-API
        response = requests.get('http://localhost:8000/api/v1/quotes', timeout=5)
        print(f"💰 Quotes API: {response.status_code}")
        if response.status_code == 200:
            quotes_data = response.json()
            print(f"   Quotes vom Backend: {len(quotes_data)}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend nicht erreichbar (localhost:8000)")
    except Exception as e:
        print(f"❌ Fehler beim API-Test: {e}")
    
    # 3. Lösungsvorschläge
    print("\n💡 LÖSUNGSVORSCHLÄGE:")
    print("=" * 30)
    
    if milestones_count == 0 and quotes_count == 0:
        print("1. 🧹 Browser-Cache leeren:")
        print("   - Firefox/Chrome: Ctrl + Shift + R")
        print("   - Oder: F12 → Rechtsklick auf Reload → 'Cache leeren'")
        print("   - Oder: Inkognito-Modus verwenden")
        
        print("\n2. 🔄 Backend neu starten:")
        print("   - Backend stoppen (Ctrl+C)")
        print("   - Backend neu starten")
        
        print("\n3. 📊 Test-Daten erstellen:")
        print("   - Gewerke über Frontend erstellen")
        print("   - Oder: Test-Skript ausführen")
        
        print("\n4. 🔍 Debug-Informationen:")
        print("   - F12 → Network-Tab → API-Calls prüfen")
        print("   - Console-Logs überprüfen")
        
    else:
        print("✅ Datenbank enthält Einträge")
        print("🔍 Prüfen Sie die API-Calls im Browser")

if __name__ == "__main__":
    check_frontend_backend_sync() 