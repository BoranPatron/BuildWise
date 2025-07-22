#!/usr/bin/env python3
"""
Analysiert die Datenquelle des Frontends
"""

import requests
import json
import os

def debug_frontend_data_source():
    """Analysiert, woher das Frontend seine Daten bekommt"""
    print("🔍 FRONTEND DATENQUELLE ANALYSE")
    print("=" * 40)
    
    # Backend-URL
    base_url = "http://localhost:8000"
    
    # 1. Backend-Verfügbarkeit prüfen
    print("\n🌐 BACKEND-VERFÜGBARKEIT:")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"   ✅ Backend erreichbar: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Backend nicht erreichbar: {e}")
        return
    
    # 2. API-Endpunkte testen
    print("\n📡 API-ENDPUNKTE TEST:")
    
    endpoints = [
        "/api/milestones/",
        "/api/quotes/",
        "/api/projects/",
        "/api/users/",
        "/api/audit-logs/"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            print(f"   {endpoint}: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print(f"      📊 {len(data)} Einträge")
                    if len(data) > 0:
                        print(f"      📋 Erster Eintrag: {data[0]}")
                elif isinstance(data, dict):
                    print(f"      📊 Dict mit {len(data)} Keys")
            elif response.status_code == 401:
                print("      🔒 Unauthorized (Token erforderlich)")
            elif response.status_code == 404:
                print("      ❌ Endpoint nicht gefunden")
                
        except Exception as e:
            print(f"   {endpoint}: ❌ Fehler - {e}")
    
    # 3. Authentifizierung testen
    print("\n🔐 AUTHENTIFIZIERUNG TEST:")
    
    # Test-Login
    login_data = {
        "email": "admin@buildwise.com",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/login", json=login_data, timeout=5)
        print(f"   Login: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            print(f"   ✅ Token erhalten: {token[:20]}...")
            
            # Mit Token API testen
            headers = {"Authorization": f"Bearer {token}"}
            
            for endpoint in endpoints:
                try:
                    response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=5)
                    print(f"   {endpoint} (mit Token): {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, list):
                            print(f"      📊 {len(data)} Einträge")
                            if len(data) > 0:
                                print(f"      📋 Erster Eintrag: {data[0]}")
                        elif isinstance(data, dict):
                            print(f"      📊 Dict mit {len(data)} Keys")
                            
                except Exception as e:
                    print(f"   {endpoint} (mit Token): ❌ Fehler - {e}")
        else:
            print(f"   ❌ Login fehlgeschlagen: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Login-Fehler: {e}")
    
    # 4. Mock-Daten prüfen
    print("\n🎭 MOCK-DATEN PRÜFUNG:")
    
    # Prüfe, ob Mock-Daten im Frontend existieren
    frontend_path = "../Frontend/Frontend/src"
    
    if os.path.exists(frontend_path):
        print(f"   📁 Frontend-Pfad: {os.path.abspath(frontend_path)}")
        
        # Suche nach Mock-Daten
        mock_files = []
        for root, dirs, files in os.walk(frontend_path):
            for file in files:
                if file.endswith(('.ts', '.tsx', '.js', '.jsx')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if 'mock' in content.lower() or 'test' in content.lower():
                                mock_files.append(file_path)
                    except:
                        pass
        
        print(f"   📋 Gefundene Mock-Dateien: {len(mock_files)}")
        for file in mock_files[:5]:  # Erste 5 zeigen
            print(f"      - {os.path.basename(file)}")
    else:
        print("   ❌ Frontend-Pfad nicht gefunden")
    
    # 5. Browser-Storage prüfen
    print("\n💾 BROWSER-STORAGE HINWEIS:")
    print("   📋 Prüfen Sie im Browser:")
    print("      - F12 → Application → Local Storage")
    print("      - F12 → Application → Session Storage")
    print("      - F12 → Application → IndexedDB")
    print("      - F12 → Network → XHR/Fetch Requests")

if __name__ == "__main__":
    debug_frontend_data_source() 