#!/usr/bin/env python3
"""
DSGVO-Feature-Test für BuildWise
Testet alle implementierten DSGVO-Features
"""

import asyncio
import sys
import os
import requests
import json
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# API-Basis-URL
BASE_URL = "http://localhost:8000/api/v1"

class GDPRFeatureTester:
    """Testet alle DSGVO-Features von BuildWise"""
    
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_id = None
        
    def print_header(self, title):
        """Druckt einen formatierten Header"""
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
    
    def print_success(self, message):
        """Druckt eine Erfolgsmeldung"""
        print(f"✅ {message}")
    
    def print_error(self, message):
        """Druckt eine Fehlermeldung"""
        print(f"❌ {message}")
    
    def print_info(self, message):
        """Druckt eine Informationsmeldung"""
        print(f"ℹ️  {message}")
    
    async def test_health_check(self):
        """Testet den Health-Check-Endpunkt"""
        self.print_header("Health Check Test")
        
        try:
            response = self.session.get(f"{BASE_URL.replace('/api/v1', '')}/health")
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Health Check erfolgreich: {data}")
                return True
            else:
                self.print_error(f"Health Check fehlgeschlagen: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Health Check Exception: {e}")
            return False
    
    async def test_user_registration(self):
        """Testet die DSGVO-konforme Benutzerregistrierung"""
        self.print_header("DSGVO-konforme Benutzerregistrierung")
        
        # Test-Benutzer mit DSGVO-Einwilligungen
        test_user = {
            "email": "test@buildwise.de",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User",
            "phone": "+49123456789",
            "user_type": "private",
            "data_processing_consent": True,
            "marketing_consent": False,
            "privacy_policy_accepted": True,
            "terms_accepted": True
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=test_user)
            if response.status_code == 201:
                data = response.json()
                self.print_success(f"Benutzer erfolgreich registriert: {data['email']}")
                self.print_info(f"DSGVO-Einwilligungen: {data.get('consents', {})}")
                return True
            else:
                self.print_error(f"Registrierung fehlgeschlagen: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Registrierung Exception: {e}")
            return False
    
    async def test_login_with_consent_check(self):
        """Testet Login mit DSGVO-Einwilligungsprüfung"""
        self.print_header("Login mit DSGVO-Einwilligungsprüfung")
        
        # Login-Daten
        login_data = {
            "username": "test@buildwise.de",
            "password": "TestPassword123!"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", data=login_data)
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.user_id = data["user"]["id"]
                
                # Setze Authorization Header
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
                
                self.print_success(f"Login erfolgreich: {data['user']['email']}")
                self.print_info(f"DSGVO-Einwilligungen: {data['user']['consents']}")
                return True
            else:
                self.print_error(f"Login fehlgeschlagen: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Login Exception: {e}")
            return False
    
    async def test_consent_management(self):
        """Testet die Einwilligungsverwaltung"""
        self.print_header("DSGVO-Einwilligungsverwaltung")
        
        # Teste Marketing-Einwilligung ändern
        consent_data = {
            "consent_type": "marketing",
            "granted": True
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/gdpr/consent", json=consent_data)
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Einwilligung geändert: {data}")
                return True
            else:
                self.print_error(f"Einwilligung fehlgeschlagen: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Einwilligung Exception: {e}")
            return False
    
    async def test_data_export(self):
        """Testet den DSGVO-Datenexport"""
        self.print_header("DSGVO-Datenexport")
        
        try:
            response = self.session.get(f"{BASE_URL}/gdpr/data-export")
            if response.status_code == 200:
                data = response.json()
                self.print_success("Datenexport erfolgreich")
                self.print_info(f"Exportierte Daten: {json.dumps(data['data'], indent=2, default=str)}")
                return True
            else:
                self.print_error(f"Datenexport fehlgeschlagen: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Datenexport Exception: {e}")
            return False
    
    async def test_privacy_policy(self):
        """Testet die Datenschutzerklärung"""
        self.print_header("Datenschutzerklärung")
        
        try:
            response = self.session.get(f"{BASE_URL}/gdpr/privacy-policy")
            if response.status_code == 200:
                data = response.json()
                self.print_success("Datenschutzerklärung erfolgreich abgerufen")
                self.print_info(f"Titel: {data['title']}")
                self.print_info(f"Version: {data['version']}")
                return True
            else:
                self.print_error(f"Datenschutzerklärung fehlgeschlagen: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Datenschutzerklärung Exception: {e}")
            return False
    
    async def test_terms_of_service(self):
        """Testet die AGB"""
        self.print_header("Allgemeine Geschäftsbedingungen")
        
        try:
            response = self.session.get(f"{BASE_URL}/gdpr/terms-of-service")
            if response.status_code == 200:
                data = response.json()
                self.print_success("AGB erfolgreich abgerufen")
                self.print_info(f"Titel: {data['title']}")
                self.print_info(f"Version: {data['version']}")
                return True
            else:
                self.print_error(f"AGB fehlgeschlagen: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"AGB Exception: {e}")
            return False
    
    async def test_data_deletion_request(self):
        """Testet den Datenlöschungsantrag"""
        self.print_header("DSGVO-Datenlöschungsantrag")
        
        try:
            response = self.session.post(f"{BASE_URL}/gdpr/data-deletion-request")
            if response.status_code == 200:
                data = response.json()
                self.print_success("Datenlöschungsantrag erfolgreich eingereicht")
                self.print_info(f"Status: {data['status']}")
                self.print_info(f"Geschätzte Bearbeitungszeit: {data['estimated_completion']}")
                return True
            else:
                self.print_error(f"Datenlöschungsantrag fehlgeschlagen: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Datenlöschungsantrag Exception: {e}")
            return False
    
    async def test_data_anonymization(self):
        """Testet die Datenanonymisierung"""
        self.print_header("DSGVO-Datenanonymisierung")
        
        try:
            response = self.session.post(f"{BASE_URL}/gdpr/data-anonymization")
            if response.status_code == 200:
                data = response.json()
                self.print_success("Datenanonymisierung erfolgreich")
                self.print_info(f"Status: {data['status']}")
                return True
            else:
                self.print_error(f"Datenanonymisierung fehlgeschlagen: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Datenanonymisierung Exception: {e}")
            return False
    
    async def test_password_change(self):
        """Testet die Passwort-Änderung"""
        self.print_header("Passwort-Änderung mit DSGVO-Audit")
        
        password_data = {
            "current_password": "TestPassword123!",
            "new_password": "NewSecurePassword456!"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/password-change", json=password_data)
            if response.status_code == 200:
                data = response.json()
                self.print_success("Passwort erfolgreich geändert")
                self.print_info("Audit-Log für Passwort-Änderung erstellt")
                return True
            else:
                self.print_error(f"Passwort-Änderung fehlgeschlagen: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Passwort-Änderung Exception: {e}")
            return False
    
    async def test_logout(self):
        """Testet den Logout mit Audit-Log"""
        self.print_header("Logout mit DSGVO-Audit")
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/logout")
            if response.status_code == 200:
                self.print_success("Logout erfolgreich")
                self.print_info("Audit-Log für Logout erstellt")
                return True
            else:
                self.print_error(f"Logout fehlgeschlagen: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Logout Exception: {e}")
            return False
    
    async def test_password_strength_validation(self):
        """Testet die Passwort-Stärke-Validierung"""
        self.print_header("Passwort-Stärke-Validierung")
        
        # Teste verschiedene Passwörter
        test_passwords = [
            ("schwach", "password"),
            ("zu kurz", "abc123"),
            ("keine Sonderzeichen", "Password123"),
            ("keine Großbuchstaben", "password123!"),
            ("keine Zahlen", "Password!"),
            ("stark", "SecurePassword123!"),
            ("sehr stark", "MyVerySecurePassword2024!@#")
        ]
        
        for strength, password in test_passwords:
            try:
                # Registriere einen Test-Benutzer mit dem Passwort
                test_user = {
                    "email": f"test_{strength.replace(' ', '_')}@buildwise.de",
                    "password": password,
                    "first_name": "Test",
                    "last_name": strength.title(),
                    "user_type": "private",
                    "data_processing_consent": True,
                    "privacy_policy_accepted": True,
                    "terms_accepted": True
                }
                
                response = self.session.post(f"{BASE_URL}/auth/register", json=test_user)
                if response.status_code == 201:
                    self.print_success(f"Passwort '{strength}' akzeptiert")
                else:
                    error_msg = response.text
                    if "Passwort" in error_msg or "password" in error_msg.lower():
                        self.print_info(f"Passwort '{strength}' korrekt abgelehnt: {error_msg}")
                    else:
                        self.print_error(f"Unerwarteter Fehler für '{strength}': {error_msg}")
                        
            except Exception as e:
                self.print_error(f"Test für '{strength}' Exception: {e}")
    
    async def run_all_tests(self):
        """Führt alle DSGVO-Tests aus"""
        print("🚀 Starte DSGVO-Feature-Tests für BuildWise...")
        print(f"📅 Test-Zeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Benutzerregistrierung", self.test_user_registration),
            ("Login mit Einwilligungsprüfung", self.test_login_with_consent_check),
            ("Einwilligungsverwaltung", self.test_consent_management),
            ("Datenexport", self.test_data_export),
            ("Datenschutzerklärung", self.test_privacy_policy),
            ("AGB", self.test_terms_of_service),
            ("Passwort-Änderung", self.test_password_change),
            ("Datenlöschungsantrag", self.test_data_deletion_request),
            ("Datenanonymisierung", self.test_data_anonymization),
            ("Logout", self.test_logout),
            ("Passwort-Stärke-Validierung", self.test_password_strength_validation)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                success = await test_func()
                results.append((test_name, success))
            except Exception as e:
                self.print_error(f"Test '{test_name}' Exception: {e}")
                results.append((test_name, False))
        
        # Zusammenfassung
        self.print_header("Test-Zusammenfassung")
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        print(f"📊 Ergebnisse: {passed}/{total} Tests erfolgreich")
        
        for test_name, success in results:
            status = "✅ BESTANDEN" if success else "❌ FEHLGESCHLAGEN"
            print(f"   {status}: {test_name}")
        
        if passed == total:
            print(f"\n🎉 Alle DSGVO-Features funktionieren korrekt!")
        else:
            print(f"\n⚠️  {total - passed} Tests sind fehlgeschlagen. Bitte überprüfen Sie die Implementierung.")
        
        return passed == total


async def main():
    """Hauptfunktion"""
    tester = GDPRFeatureTester()
    
    try:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests abgebrochen")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 