#!/usr/bin/env python3
"""
Test-Script für den E-Mail-Service
"""

import asyncio
import sys
import os
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.email_service import email_service


async def test_email_service():
    """Testet den E-Mail-Service"""
    
    print("🧪 Teste E-Mail-Service...")
    
    # Test-E-Mail-Adresse
    test_email = "test@example.com"
    test_name = "Max Mustermann"
    test_token = "test-verification-token-12345"
    
    try:
        # Test 1: Verifizierungs-E-Mail
        print("\n📧 Teste Verifizierungs-E-Mail...")
        success = email_service.send_verification_email(
            test_email, test_token, test_name
        )
        if success:
            print("✅ Verifizierungs-E-Mail erfolgreich gesendet")
        else:
            print("❌ Verifizierungs-E-Mail fehlgeschlagen")
        
        # Test 2: Passwort-Reset-E-Mail
        print("\n📧 Teste Passwort-Reset-E-Mail...")
        success = email_service.send_password_reset_email(
            test_email, test_token, test_name
        )
        if success:
            print("✅ Passwort-Reset-E-Mail erfolgreich gesendet")
        else:
            print("❌ Passwort-Reset-E-Mail fehlgeschlagen")
        
        # Test 3: Willkommens-E-Mail
        print("\n📧 Teste Willkommens-E-Mail...")
        success = email_service.send_welcome_email(
            test_email, test_name, "Bauträger"
        )
        if success:
            print("✅ Willkommens-E-Mail erfolgreich gesendet")
        else:
            print("❌ Willkommens-E-Mail fehlgeschlagen")
        
        # Test 4: Kontolöschungs-E-Mail
        print("\n📧 Teste Kontolöschungs-E-Mail...")
        success = email_service.send_account_deletion_email(
            test_email, test_name
        )
        if success:
            print("✅ Kontolöschungs-E-Mail erfolgreich gesendet")
        else:
            print("❌ Kontolöschungs-E-Mail fehlgeschlagen")
        
        print("\n🎉 E-Mail-Service-Tests abgeschlossen!")
        
    except Exception as e:
        print(f"❌ Fehler beim Testen des E-Mail-Services: {e}")


if __name__ == "__main__":
    asyncio.run(test_email_service()) 