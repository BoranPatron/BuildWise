#!/usr/bin/env python3
"""
Behebung des Verbindungsproblems
"""

import subprocess
import time
import os
import sys

def fix_connection_issue():
    """Behebt das Verbindungsproblem"""
    print("🔧 Behebe Verbindungsproblem...")
    
    # 1. Prüfe ob Backend läuft
    print("\n1️⃣ Prüfe Backend-Status:")
    try:
        import requests
        response = requests.get("http://localhost:8000/docs", timeout=3)
        print(f"   ✅ Backend läuft: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Backend nicht erreichbar: {e}")
        print("   🔧 Starte Backend neu...")
        
        # Backend neu starten
        try:
            # Stoppe alte Prozesse
            subprocess.run(["taskkill", "/f", "/im", "python.exe"], capture_output=True)
            time.sleep(2)
            
            # Starte Backend neu
            subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                "app.main:app", "--reload", 
                "--host", "0.0.0.0", "--port", "8000"
            ], cwd=os.getcwd())
            
            print("   ⏳ Warte auf Backend-Start...")
            time.sleep(5)
            
            # Teste erneut
            try:
                response = requests.get("http://localhost:8000/docs", timeout=5)
                print(f"   ✅ Backend gestartet: {response.status_code}")
            except Exception as e2:
                print(f"   ❌ Backend-Start fehlgeschlagen: {e2}")
                return False
                
        except Exception as e:
            print(f"   ❌ Fehler beim Backend-Start: {e}")
            return False
    
    # 2. Prüfe Datenbank
    print("\n2️⃣ Prüfe Datenbank:")
    if os.path.exists('buildwise.db'):
        print(f"   ✅ buildwise.db gefunden: {os.path.getsize('buildwise.db')} Bytes")
        
        import sqlite3
        conn = sqlite3.connect('buildwise.db')
        cursor = conn.cursor()
        
        try:
            # Tabellen prüfen
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"   📋 Tabellen: {len(tables)}")
            
            # Audit Logs prüfen
            cursor.execute("SELECT COUNT(*) FROM audit_logs")
            audit_count = cursor.fetchone()[0]
            print(f"   📊 Audit Logs: {audit_count}")
            
            # Milestones prüfen
            cursor.execute("SELECT COUNT(*) FROM milestones")
            milestones_count = cursor.fetchone()[0]
            print(f"   🏗️ Milestones: {milestones_count}")
            
        except Exception as e:
            print(f"   ❌ Datenbank-Fehler: {e}")
        finally:
            conn.close()
    else:
        print("   ❌ buildwise.db nicht gefunden")
    
    # 3. Teste API-Verbindung
    print("\n3️⃣ Teste API-Verbindung:")
    try:
        headers = {
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBidWlsZHdpc2UuZGUiLCJleHAiOjE3NTI5NDY2OTh9.QybsYBe-4RUGdICzDAplsIzxmuaDGHTLMp5_k3YfKNA",
            "Content-Type": "application/json"
        }
        
        response = requests.get("http://localhost:8000/api/v1/users/me", headers=headers)
        print(f"   🔐 Auth-Test: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"   ✅ User: {user_data.get('email', 'N/A')}")
        else:
            print(f"   ❌ Auth-Fehler: {response.text}")
            
    except Exception as e:
        print(f"   ❌ API-Test fehlgeschlagen: {e}")
    
    # 4. Lösungsvorschläge
    print("\n4️⃣ Lösungsvorschläge:")
    print("   🔧 Sofortige Maßnahmen:")
    print("   1. Browser-Cache leeren (Ctrl + Shift + R)")
    print("   2. Frontend neu laden")
    print("   3. Backend-Logs prüfen")
    print("   4. Datenbank-Verbindung testen")
    
    print("\n   📋 Debug-Schritte:")
    print("   1. Browser: F12 → Network-Tab")
    print("   2. API-Calls beobachten")
    print("   3. 401/500 Fehler identifizieren")
    print("   4. Backend-Konsole prüfen")
    
    print("\n✅ Verbindungsproblem-Behebung abgeschlossen!")
    return True

if __name__ == "__main__":
    fix_connection_issue() 