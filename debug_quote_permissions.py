#!/usr/bin/env python3
"""
BuildWise - Quote Permissions Debug Script
==========================================

Dieses Skript analysiert und behebt Probleme mit den Berechtigungen
beim Annehmen von Angeboten (403 Forbidden Fehler).

Problem: 
- Beim Klick auf "Angebot annehmen" wird ein 403-Fehler zurückgegeben
- Backend prüft: user_id == quote.project.owner_id
- Nur der Projekt-Eigentümer darf Angebote annehmen

Lösung:
- Überprüfung der User-IDs und Projekt-Owner-IDs
- Korrektur der Projekt-Owner-Zuordnung
- Test der API-Endpunkte
"""

import requests
import json
import sys
from datetime import datetime

# Konfiguration
API_BASE_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin@buildwise.de"
ADMIN_PASSWORD = "admin123"

def log(message, level="INFO"):
    """Logging mit Zeitstempel"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def get_auth_token():
    """Authentifizierung und Token-Erhalt"""
    try:
        # OAuth2PasswordRequestForm erwartet username und password als form data
        login_data = {
            "username": ADMIN_EMAIL,  # OAuth2 verwendet 'username' statt 'email'
            "password": ADMIN_PASSWORD
        }
        
        response = requests.post(f"{API_BASE_URL}/auth/login", data=login_data)
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            log(f"✅ Token erfolgreich erhalten: {token[:20]}...")
            return token
        else:
            log(f"❌ Login fehlgeschlagen: {response.status_code} - {response.text}", "ERROR")
            return None
            
    except Exception as e:
        log(f"❌ Fehler beim Login: {str(e)}", "ERROR")
        return None

def get_user_info(token):
    """Aktuelle User-Informationen abrufen"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE_URL}/users/me", headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            log(f"✅ User-Info abgerufen: ID={user_data.get('id')}, Email={user_data.get('email')}")
            return user_data
        else:
            log(f"❌ User-Info fehlgeschlagen: {response.status_code}", "ERROR")
            return None
            
    except Exception as e:
        log(f"❌ Fehler beim Abrufen der User-Info: {str(e)}", "ERROR")
        return None

def get_projects(token):
    """Alle Projekte abrufen"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE_URL}/projects", headers=headers)
        
        if response.status_code == 200:
            projects = response.json()
            log(f"✅ {len(projects)} Projekte abgerufen")
            return projects
        else:
            log(f"❌ Projekte abrufen fehlgeschlagen: {response.status_code}", "ERROR")
            return []
            
    except Exception as e:
        log(f"❌ Fehler beim Abrufen der Projekte: {str(e)}", "ERROR")
        return []

def get_quotes(token, project_id=None):
    """Angebote abrufen (optional für ein spezifisches Projekt)"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        params = {"project_id": project_id} if project_id else {}
        response = requests.get(f"{API_BASE_URL}/quotes", headers=headers, params=params)
        
        if response.status_code == 200:
            quotes = response.json()
            log(f"✅ {len(quotes)} Angebote abgerufen")
            return quotes
        else:
            log(f"❌ Angebote abrufen fehlgeschlagen: {response.status_code}", "ERROR")
            return []
            
    except Exception as e:
        log(f"❌ Fehler beim Abrufen der Angebote: {str(e)}", "ERROR")
        return []

def analyze_quote_permissions(token, user_data, projects, quotes):
    """Analyse der Angebot-Berechtigungen"""
    log("🔍 Analysiere Angebot-Berechtigungen...")
    
    user_id = user_data.get('id')
    log(f"📋 Aktueller User: ID={user_id}, Email={user_data.get('email')}")
    
    # Projekte mit Owner-Informationen
    log("\n📊 Projekte und deren Owner:")
    for project in projects:
        owner_id = project.get('owner_id')
        log(f"  Projekt {project.get('id')}: '{project.get('name')}' - Owner ID: {owner_id}")
        
        if owner_id != user_id:
            log(f"    ⚠️  WARNUNG: User {user_id} ist NICHT der Owner von Projekt {project.get('id')}")
    
    # Angebote mit Projekt-Zuordnung
    log("\n📊 Angebote und deren Projekte:")
    for quote in quotes:
        quote_id = quote.get('id')
        project_id = quote.get('project_id')
        status = quote.get('status')
        
        # Finde das zugehörige Projekt
        project = next((p for p in projects if p.get('id') == project_id), None)
        project_owner_id = project.get('owner_id') if project else None
        
        log(f"  Angebot {quote_id}: Projekt {project_id}, Status: {status}")
        log(f"    Projekt Owner: {project_owner_id}, User ID: {user_id}")
        
        if project_owner_id != user_id:
            log(f"    ❌ PROBLEM: User {user_id} kann Angebot {quote_id} NICHT annehmen!")
        else:
            log(f"    ✅ OK: User {user_id} kann Angebot {quote_id} annehmen")

def test_accept_quote(token, quote_id):
    """Test: Angebot annehmen"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{API_BASE_URL}/quotes/{quote_id}/accept", headers=headers)
        
        if response.status_code == 200:
            log(f"✅ Angebot {quote_id} erfolgreich angenommen!")
            return True
        else:
            log(f"❌ Angebot {quote_id} annehmen fehlgeschlagen: {response.status_code} - {response.text}", "ERROR")
            return False
            
    except Exception as e:
        log(f"❌ Fehler beim Annehmen des Angebots {quote_id}: {str(e)}", "ERROR")
        return False

def fix_project_ownership(token, project_id, new_owner_id):
    """Projekt-Owner korrigieren (nur für Debug-Zwecke)"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        data = {"owner_id": new_owner_id}
        
        response = requests.put(f"{API_BASE_URL}/projects/{project_id}", headers=headers, json=data)
        
        if response.status_code == 200:
            log(f"✅ Projekt {project_id} Owner auf User {new_owner_id} geändert")
            return True
        else:
            log(f"❌ Projekt Owner ändern fehlgeschlagen: {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        log(f"❌ Fehler beim Ändern des Projekt-Owners: {str(e)}", "ERROR")
        return False

def main():
    """Hauptfunktion"""
    log("🚀 Starte BuildWise Quote Permissions Debug Script")
    log("=" * 60)
    
    # 1. Authentifizierung
    token = get_auth_token()
    if not token:
        log("❌ Authentifizierung fehlgeschlagen. Script wird beendet.", "ERROR")
        sys.exit(1)
    
    # 2. User-Informationen abrufen
    user_data = get_user_info(token)
    if not user_data:
        log("❌ User-Informationen konnten nicht abgerufen werden.", "ERROR")
        sys.exit(1)
    
    # 3. Projekte abrufen
    projects = get_projects(token)
    if not projects:
        log("❌ Keine Projekte gefunden.", "ERROR")
        sys.exit(1)
    
    # 4. Angebote abrufen
    quotes = get_quotes(token)
    if not quotes:
        log("❌ Keine Angebote gefunden.", "ERROR")
        sys.exit(1)
    
    # 5. Berechtigungen analysieren
    analyze_quote_permissions(token, user_data, projects, quotes)
    
    # 6. Test: Angebot annehmen
    log("\n🧪 Teste Angebot annehmen...")
    if quotes:
        first_quote = quotes[0]
        quote_id = first_quote.get('id')
        project_id = first_quote.get('project_id')
        
        # Finde das zugehörige Projekt
        project = next((p for p in projects if p.get('id') == project_id), None)
        project_owner_id = project.get('owner_id') if project else None
        user_id = user_data.get('id')
        
        if project_owner_id != user_id:
            log(f"⚠️  User {user_id} ist nicht Owner von Projekt {project_id}")
            log(f"   Projekt Owner: {project_owner_id}")
            
            # Frage nach Korrektur
            response = input(f"\nSoll der Owner von Projekt {project_id} auf User {user_id} geändert werden? (j/N): ")
            if response.lower() in ['j', 'ja', 'y', 'yes']:
                if fix_project_ownership(token, project_id, user_id):
                    log("✅ Projekt-Owner korrigiert. Teste erneut...")
                    test_accept_quote(token, quote_id)
        else:
            log(f"✅ User {user_id} ist Owner von Projekt {project_id}. Teste Angebot annehmen...")
            test_accept_quote(token, quote_id)
    
    log("\n🏁 Debug-Script abgeschlossen")

if __name__ == "__main__":
    main() 