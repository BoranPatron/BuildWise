#!/usr/bin/env python3
"""
Test-Skript für den vollständigen Abnahme-Rechnung-Bewertung Workflow
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Konfiguration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

class WorkflowTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_data = {}
        
    def login(self, email: str, password: str):
        """Login und Token holen"""
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json={
                "email": email,
                "password": password
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                print(f"✅ Login erfolgreich für {email}")
                return True
            else:
                print(f"❌ Login fehlgeschlagen: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Login-Fehler: {e}")
            return False
    
    def test_health(self):
        """Test Backend-Health"""
        try:
            response = self.session.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("✅ Backend ist gesund")
                return True
            else:
                print(f"❌ Backend-Health-Fehler: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health-Check-Fehler: {e}")
            return False
    
    def test_acceptance_workflow(self):
        """Test Abnahme-Workflow"""
        print("\n🧪 Teste Abnahme-Workflow...")
        
        # Test-Daten für Abnahme
        acceptance_data = {
            "accepted": True,
            "acceptanceNotes": "Test-Abnahme erfolgreich",
            "contractorNotes": "Qualität entspricht Anforderungen",
            "qualityRating": 5,
            "timelinessRating": 5,
            "overallRating": 5,
            "photos": [],
            "defects": [],
            "milestone_id": 1  # Test-Meilenstein
        }
        
        try:
            response = self.session.post(f"{API_BASE}/acceptance/complete", json=acceptance_data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Abnahme erfolgreich: {result.get('id')}")
                self.test_data['acceptance_id'] = result.get('id')
                return True
            else:
                print(f"❌ Abnahme-Fehler: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Abnahme-Workflow-Fehler: {e}")
            return False
    
    def test_invoice_creation(self):
        """Test Rechnungserstellung"""
        print("\n🧪 Teste Rechnungserstellung...")
        
        invoice_data = {
            "milestone_id": 1,
            "invoice_number": f"INV-{int(time.time())}",
            "invoice_date": datetime.now().isoformat(),
            "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "total_amount": 5000.00,
            "net_amount": 4201.68,
            "vat_rate": 19.0,
            "vat_amount": 798.32,
            "description": "Test-Rechnung für Abnahme-Workflow",
            "type": "manual"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/invoices/create", json=invoice_data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Rechnung erstellt: {result.get('invoice_number')}")
                self.test_data['invoice_id'] = result.get('id')
                return True
            else:
                print(f"❌ Rechnungserstellung-Fehler: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Rechnungserstellung-Fehler: {e}")
            return False
    
    def test_invoice_payment(self):
        """Test Rechnungsbezahlung"""
        if not self.test_data.get('invoice_id'):
            print("⚠️ Keine Rechnung-ID verfügbar")
            return False
            
        print("\n🧪 Teste Rechnungsbezahlung...")
        
        payment_data = {
            "payment_reference": f"PAY-{int(time.time())}",
            "payment_method": "bank_transfer",
            "notes": "Test-Zahlung"
        }
        
        try:
            response = self.session.post(
                f"{API_BASE}/invoices/{self.test_data['invoice_id']}/mark-paid", 
                json=payment_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Rechnung als bezahlt markiert: {result.get('status')}")
                return True
            else:
                print(f"❌ Rechnungsbezahlung-Fehler: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Rechnungsbezahlung-Fehler: {e}")
            return False
    
    def test_service_provider_rating(self):
        """Test Service Provider Bewertung"""
        print("\n🧪 Teste Service Provider Bewertung...")
        
        rating_data = {
            "service_provider_id": 1,  # Test-Service-Provider
            "milestone_id": 1,
            "quality_rating": 5,
            "timeliness_rating": 5,
            "communication_rating": 5,
            "overall_rating": 5,
            "notes": "Sehr zufrieden mit der Leistung"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/ratings/", json=rating_data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Bewertung erstellt: {result.get('id')}")
                return True
            else:
                print(f"❌ Bewertung-Fehler: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Bewertung-Fehler: {e}")
            return False
    
    def test_invoice_retrieval(self):
        """Test Rechnungsabruf"""
        print("\n🧪 Teste Rechnungsabruf...")
        
        try:
            response = self.session.get(f"{API_BASE}/invoices/milestone/1")
            
            if response.status_code == 200:
                result = response.json()
                if result:
                    print(f"✅ Rechnung gefunden: {result.get('invoice_number')}")
                    return True
                else:
                    print("ℹ️ Keine Rechnung für Meilenstein gefunden")
                    return True
            else:
                print(f"❌ Rechnungsabruf-Fehler: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Rechnungsabruf-Fehler: {e}")
            return False
    
    def run_complete_test(self):
        """Führe vollständigen Test durch"""
        print("🚀 Starte vollständigen Abnahme-Rechnung-Bewertung Workflow Test")
        print("=" * 60)
        
        # 1. Health Check
        if not self.test_health():
            return False
        
        # 2. Login (Test-Account)
        if not self.login("test@buildwise.com", "test123"):
            print("⚠️ Verwende anonyme Tests (ohne Login)")
        
        # 3. Abnahme-Workflow
        if not self.test_acceptance_workflow():
            print("⚠️ Abnahme-Workflow fehlgeschlagen")
        
        # 4. Rechnungserstellung
        if not self.test_invoice_creation():
            print("⚠️ Rechnungserstellung fehlgeschlagen")
        
        # 5. Rechnungsabruf
        if not self.test_invoice_retrieval():
            print("⚠️ Rechnungsabruf fehlgeschlagen")
        
        # 6. Rechnungsbezahlung
        if not self.test_invoice_payment():
            print("⚠️ Rechnungsbezahlung fehlgeschlagen")
        
        # 7. Service Provider Bewertung
        if not self.test_service_provider_rating():
            print("⚠️ Service Provider Bewertung fehlgeschlagen")
        
        print("\n" + "=" * 60)
        print("✅ Vollständiger Workflow-Test abgeschlossen")
        print(f"📊 Test-Daten: {self.test_data}")
        
        return True

def main():
    """Hauptfunktion"""
    tester = WorkflowTester()
    tester.run_complete_test()

if __name__ == "__main__":
    main() 