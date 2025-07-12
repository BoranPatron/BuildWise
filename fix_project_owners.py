#!/usr/bin/env python3
"""
BuildWise - Fix Project Owners Script
=====================================

Dieses Skript korrigiert automatisch die Projekt-Owner-Zuordnung,
damit der eingeloggte Admin-User alle Angebote annehmen kann.

Problem:
- Projekte haben möglicherweise falsche owner_id Werte
- Admin-User kann Angebote nicht annehmen (403 Forbidden)

Lösung:
- Setze owner_id für alle Projekte auf den Admin-User
- Teste die Korrektur durch Angebot-Annahme
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

def fix_project_owner(token, project_id, new_owner_id):
    """Projekt-Owner korrigieren"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        data = {"owner_id": new_owner_id}
        
        response = requests.put(f"{API_BASE_URL}/projects/{project_id}", headers=headers, json=data)
        
        if response.status_code == 200:
            log(f"✅ Projekt {project_id} Owner auf User {new_owner_id} geändert")
            return True
        else:
            log(f"❌ Projekt {project_id} Owner ändern fehlgeschlagen: {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        log(f"❌ Fehler beim Ändern des Projekt-Owners: {str(e)}", "ERROR")
        return False

def get_quotes_for_project(token, project_id):
    """Angebote für ein spezifisches Projekt abrufen"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        params = {"project_id": project_id}
        response = requests.get(f"{API_BASE_URL}/quotes", headers=headers, params=params)
        
        if response.status_code == 200:
            quotes = response.json()
            return quotes
        else:
            log(f"❌ Angebote für Projekt {project_id} abrufen fehlgeschlagen: {response.status_code}", "ERROR")
            return []
            
    except Exception as e:
        log(f"❌ Fehler beim Abrufen der Angebote: {str(e)}", "ERROR")
        return []

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

def main():
    """Hauptfunktion"""
    log("🚀 Starte BuildWise Fix Project Owners Script")
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
    
    user_id = user_data.get('id')
    log(f"📋 Admin User: ID={user_id}, Email={user_data.get('email')}")
    
    # 3. Projekte abrufen
    projects = get_projects(token)
    if not projects:
        log("❌ Keine Projekte gefunden.", "ERROR")
        sys.exit(1)
    
    # 4. Projekte analysieren und korrigieren
    log("\n🔍 Analysiere Projekte...")
    projects_to_fix = []
    
    for project in projects:
        project_id = project.get('id')
        project_name = project.get('name')
        current_owner_id = project.get('owner_id')
        
        log(f"  Projekt {project_id}: '{project_name}' - Owner: {current_owner_id}")
        
        if current_owner_id != user_id:
            log(f"    ⚠️  Owner muss korrigiert werden: {current_owner_id} → {user_id}")
            projects_to_fix.append(project)
        else:
            log(f"    ✅ Owner ist bereits korrekt")
    
    # 5. Projekte korrigieren
    if projects_to_fix:
        log(f"\n🔧 Korrigiere {len(projects_to_fix)} Projekte...")
        
        for project in projects_to_fix:
            project_id = project.get('id')
            project_name = project.get('name')
            
            log(f"  Korrigiere Projekt {project_id}: '{project_name}'")
            if fix_project_owner(token, project_id, user_id):
                log(f"    ✅ Projekt {project_id} korrigiert")
            else:
                log(f"    ❌ Projekt {project_id} Korrektur fehlgeschlagen")
    else:
        log("\n✅ Alle Projekte haben bereits den korrekten Owner")
    
    # 6. Test: Angebot annehmen
    log("\n🧪 Teste Angebot annehmen...")
    
    # Finde ein Projekt mit Angeboten
    test_project = None
    test_quote = None
    
    for project in projects:
        project_id = project.get('id')
        quotes = get_quotes_for_project(token, project_id)
        
        if quotes:
            # Finde ein Angebot mit Status 'submitted' oder 'under_review'
            for quote in quotes:
                status = quote.get('status')
                if status in ['submitted', 'under_review']:
                    test_project = project
                    test_quote = quote
                    break
        
        if test_quote:
            break
    
    if test_quote:
        quote_id = test_quote.get('id')
        project_id = test_quote.get('project_id')
        status = test_quote.get('status')
        
        log(f"  Teste Angebot {quote_id} (Projekt {project_id}, Status: {status})")
        
        if test_accept_quote(token, quote_id):
            log("✅ Test erfolgreich! Angebot konnte angenommen werden.")
        else:
            log("❌ Test fehlgeschlagen! Angebot konnte nicht angenommen werden.")
    else:
        log("⚠️  Kein geeignetes Angebot zum Testen gefunden")
        log("   (Suche nach Angeboten mit Status 'submitted' oder 'under_review')")
    
    log("\n🏁 Fix Project Owners Script abgeschlossen")

if __name__ == "__main__":
    main() 