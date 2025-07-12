#!/usr/bin/env python3
"""
BuildWise - API Check Script für alle Angebote
==============================================

Dieses Skript ruft alle Angebote im System ab und zeigt detaillierte Informationen an.
Ziel: Schnelle Diagnose, warum das Debug-Skript keine Angebote findet.
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

def get_all_quotes(token):
    """Alle Angebote ohne Filter abrufen"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Versuche verschiedene Endpunkte
        endpoints = [
            "/quotes",
            "/quotes/",
            "/quotes?limit=100",
            "/quotes?all=true"
        ]
        
        for endpoint in endpoints:
            try:
                log(f"🔍 Versuche Endpunkt: {endpoint}")
                response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers)
                
                if response.status_code == 200:
                    quotes = response.json()
                    log(f"✅ {len(quotes)} Angebote über {endpoint} gefunden")
                    return quotes, endpoint
                else:
                    log(f"⚠️ Endpunkt {endpoint} fehlgeschlagen: {response.status_code}")
                    
            except Exception as e:
                log(f"⚠️ Fehler bei Endpunkt {endpoint}: {str(e)}")
        
        log("❌ Kein Endpunkt funktioniert", "ERROR")
        return [], None
            
    except Exception as e:
        log(f"❌ Fehler beim Abrufen der Angebote: {str(e)}", "ERROR")
        return [], None

def get_all_projects(token):
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

def analyze_quotes(quotes, projects, endpoint_used):
    """Detaillierte Analyse der Angebote"""
    log("🔍 Analysiere Angebote...")
    log(f"📊 Endpunkt verwendet: {endpoint_used}")
    log(f"📊 Anzahl Angebote: {len(quotes)}")
    
    if not quotes:
        log("❌ Keine Angebote gefunden!")
        return
    
    # Erstelle Projekt-Lookup
    project_lookup = {p['id']: p for p in projects}
    
    log("\n📋 DETAILLIERTE ANGEBOTS-ANALYSE:")
    log("=" * 60)
    
    for i, quote in enumerate(quotes, 1):
        log(f"\n📄 Angebot {i}:")
        log(f"  ID: {quote.get('id')}")
        log(f"  Titel: {quote.get('title', 'N/A')}")
        log(f"  Status: {quote.get('status', 'N/A')}")
        log(f"  Projekt-ID: {quote.get('project_id', 'N/A')}")
        log(f"  Dienstleister-ID: {quote.get('service_provider_id', 'N/A')}")
        log(f"  Betrag: {quote.get('total_amount', 'N/A')} {quote.get('currency', 'EUR')}")
        log(f"  Erstellt: {quote.get('created_at', 'N/A')}")
        log(f"  Aktualisiert: {quote.get('updated_at', 'N/A')}")
        
        # Projekt-Info
        project_id = quote.get('project_id')
        if project_id and project_id in project_lookup:
            project = project_lookup[project_id]
            log(f"  Projekt: {project.get('name', 'N/A')} (Owner: {project.get('owner_id', 'N/A')})")
        else:
            log(f"  Projekt: Nicht gefunden (ID: {project_id})")
        
        # Zusätzliche Felder
        if quote.get('company_name'):
            log(f"  Firma: {quote.get('company_name')}")
        if quote.get('contact_person'):
            log(f"  Ansprechpartner: {quote.get('contact_person')}")
        if quote.get('email'):
            log(f"  E-Mail: {quote.get('email')}")
    
    # Statistiken
    log("\n📊 STATISTIKEN:")
    log("=" * 30)
    
    status_counts = {}
    project_counts = {}
    
    for quote in quotes:
        status = quote.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
        
        project_id = quote.get('project_id')
        if project_id:
            project_counts[project_id] = project_counts.get(project_id, 0) + 1
    
    log(f"Status-Verteilung:")
    for status, count in status_counts.items():
        log(f"  {status}: {count}")
    
    log(f"Projekt-Verteilung:")
    for project_id, count in project_counts.items():
        project_name = project_lookup.get(project_id, {}).get('name', 'Unbekannt')
        log(f"  Projekt {project_id} ({project_name}): {count} Angebote")

def get_quote_by_id(token, quote_id):
    """Hole ein Angebot gezielt per ID"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE_URL}/quotes/{quote_id}", headers=headers)
        if response.status_code == 200:
            quote = response.json()
            log(f"\n✅ Angebot mit ID {quote_id} gefunden:")
            log(json.dumps(quote, indent=2, ensure_ascii=False))
            return quote
        else:
            log(f"❌ Angebot mit ID {quote_id} nicht gefunden: {response.status_code}", "ERROR")
            return None
    except Exception as e:
        log(f"❌ Fehler beim Abrufen des Angebots {quote_id}: {str(e)}", "ERROR")
        return None

def main():
    """Hauptfunktion"""
    log("🚀 Starte BuildWise API Check Script")
    log("=" * 50)
    
    # 1. Authentifizierung
    token = get_auth_token()
    if not token:
        log("❌ Authentifizierung fehlgeschlagen. Script wird beendet.", "ERROR")
        sys.exit(1)
    
    # 2. Alle Angebote abrufen
    quotes, endpoint_used = get_all_quotes(token)
    
    # 3. Alle Projekte abrufen
    projects = get_all_projects(token)
    
    # 4. Detaillierte Analyse
    analyze_quotes(quotes, projects, endpoint_used)
    
    # 5. Test: Angebot mit ID 1 gezielt abrufen
    get_quote_by_id(token, 1)

    log("\n✅ API Check abgeschlossen!")

if __name__ == "__main__":
    main() 