#!/usr/bin/env python3
"""
Debug-Skript zur Überprüfung der Frontend-Backend-Diskrepanz
"""

import sqlite3
import requests
import json
import os

def check_database_directly():
    """Überprüft die Datenbank direkt"""
    print("🔍 Überprüfe Datenbank direkt...")
    
    if not os.path.exists('buildwise.db'):
        print("❌ buildwise.db nicht gefunden!")
        return
    
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    try:
        # Prüfe milestones Tabelle
        cursor.execute("SELECT COUNT(*) FROM milestones")
        milestones_count = cursor.fetchone()[0]
        print(f"📊 Milestones in DB: {milestones_count}")
        
        if milestones_count > 0:
            cursor.execute("SELECT id, title, description, status FROM milestones LIMIT 5")
            milestones = cursor.fetchall()
            print("📋 Milestones Details:")
            for m in milestones:
                print(f"  - ID {m[0]}: '{m[1]}' (Status: {m[3]})")
        
        # Prüfe quotes Tabelle
        cursor.execute("SELECT COUNT(*) FROM quotes")
        quotes_count = cursor.fetchone()[0]
        print(f"📊 Quotes in DB: {quotes_count}")
        
        # Prüfe projects Tabelle
        cursor.execute("SELECT COUNT(*) FROM projects")
        projects_count = cursor.fetchone()[0]
        print(f"📊 Projects in DB: {projects_count}")
        
        if projects_count > 0:
            cursor.execute("SELECT id, name FROM projects LIMIT 3")
            projects = cursor.fetchall()
            print("📋 Projects Details:")
            for p in projects:
                print(f"  - ID {p[0]}: '{p[1]}'")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Fehler bei DB-Überprüfung: {e}")
        conn.close()

def check_backend_api():
    """Überprüft die Backend-API"""
    print("\n🔍 Überprüfe Backend-API...")
    
    try:
        # Teste Backend-Verfügbarkeit
        response = requests.get('http://localhost:8000/docs', timeout=5)
        print("✅ Backend läuft auf http://localhost:8000")
        
        # Teste Milestones-API ohne Auth
        try:
            response = requests.get('http://localhost:8000/api/v1/milestones/all', timeout=5)
            print(f"📡 Milestones API Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"📊 Milestones von API: {len(data)}")
                for i, milestone in enumerate(data[:3]):
                    print(f"  - {i+1}: '{milestone.get('title', 'N/A')}' (Status: {milestone.get('status', 'N/A')})")
            else:
                print(f"❌ API-Fehler: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ API-Call fehlgeschlagen: {e}")
        
        # Teste mit Auth-Token (falls vorhanden)
        print("\n🔐 Teste mit Authentifizierung...")
        
        # Simuliere Login
        login_data = {
            "username": "admin@buildwise.com",
            "password": "admin123"
        }
        
        try:
            login_response = requests.post('http://localhost:8000/api/v1/auth/login', 
                                        json=login_data, timeout=5)
            
            if login_response.status_code == 200:
                token_data = login_response.json()
                token = token_data.get('access_token')
                print("✅ Login erfolgreich")
                
                # Teste Milestones mit Token
                headers = {'Authorization': f'Bearer {token}'}
                milestones_response = requests.get('http://localhost:8000/api/v1/milestones/all', 
                                               headers=headers, timeout=5)
                
                print(f"📡 Authentifizierte Milestones API: {milestones_response.status_code}")
                if milestones_response.status_code == 200:
                    data = milestones_response.json()
                    print(f"📊 Milestones mit Auth: {len(data)}")
                    for i, milestone in enumerate(data[:3]):
                        print(f"  - {i+1}: '{milestone.get('title', 'N/A')}' (Status: {milestone.get('status', 'N/A')})")
                else:
                    print(f"❌ Auth API-Fehler: {milestones_response.status_code}")
                    print(f"Response: {milestones_response.text}")
            else:
                print(f"❌ Login fehlgeschlagen: {login_response.status_code}")
                print(f"Response: {login_response.text}")
                
        except Exception as e:
            print(f"❌ Auth-Test fehlgeschlagen: {e}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Backend nicht erreichbar auf http://localhost:8000")
    except Exception as e:
        print(f"❌ Backend-Test fehlgeschlagen: {e}")

def check_frontend_cache():
    """Überprüft mögliche Frontend-Cache-Probleme"""
    print("\n🔍 Frontend-Cache-Analyse...")
    
    print("💡 Mögliche Ursachen für die Diskrepanz:")
    print("1. Browser-Cache: Frontend zeigt gecachte Daten")
    print("2. Mock-Daten: Frontend verwendet Test-Daten")
    print("3. Falsche API-URL: Frontend verbindet sich mit anderem Backend")
    print("4. CORS-Probleme: API-Calls werden blockiert")
    print("5. Auth-Probleme: Token ist ungültig")
    
    print("\n🔧 Lösungsvorschläge:")
    print("1. Browser-Cache leeren (Ctrl+Shift+R)")
    print("2. Entwicklertools öffnen und Network-Tab prüfen")
    print("3. Backend-Logs überprüfen")
    print("4. API-Calls im Browser debuggen")

def main():
    print("🔍 Frontend-Backend-Diskrepanz Debug")
    print("=" * 50)
    
    check_database_directly()
    check_backend_api()
    check_frontend_cache()
    
    print("\n" + "=" * 50)
    print("🎯 Nächste Schritte:")
    print("1. Browser-Cache leeren")
    print("2. Entwicklertools öffnen (F12)")
    print("3. Network-Tab prüfen bei API-Calls")
    print("4. Backend-Logs überprüfen")
    print("5. API-Endpunkte direkt testen")

if __name__ == "__main__":
    main() 