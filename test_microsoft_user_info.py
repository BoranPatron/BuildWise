#!/usr/bin/env python3
"""
Test-Skript für Microsoft User Info Debugging
"""

import asyncio
import aiohttp
from app.core.config import settings

async def test_microsoft_user_info():
    """Testet die Microsoft User Info API"""
    
    print("🔍 Microsoft User Info Debug")
    print("=" * 50)
    
    # Simuliere eine Microsoft Graph API-Antwort
    sample_responses = [
        {
            "id": "12345678-1234-1234-1234-123456789012",
            "displayName": "Test User",
            "givenName": "Test",
            "surname": "User",
            "userPrincipalName": "test@example.com",
            "mail": "test@example.com",
            "email": "test@example.com"
        },
        {
            "id": "12345678-1234-1234-1234-123456789012",
            "displayName": "Test User",
            "givenName": "Test",
            "surname": "User",
            "userPrincipalName": "test@example.com",
            "mail": None,
            "email": None
        },
        {
            "id": "12345678-1234-1234-1234-123456789012",
            "displayName": "Test User",
            "givenName": "Test",
            "surname": "User",
            "userPrincipalName": "test@example.onmicrosoft.com",
            "mail": "test@example.com",
            "email": None
        }
    ]
    
    for i, user_info in enumerate(sample_responses, 1):
        print(f"\n📋 Test {i}:")
        print(f"  - User-Info: {user_info}")
        
        # Teste E-Mail-Extraktion
        email = (
            user_info.get("email") or
            user_info.get("mail") or
            user_info.get("userPrincipalName") or
            user_info.get("upn")
        )
        
        if email and "@" in email and not email.endswith(".onmicrosoft.com"):
            print(f"  ✅ E-Mail gefunden: {email}")
        elif email and email.endswith(".onmicrosoft.com"):
            email = user_info.get("email") or user_info.get("mail")
            if email:
                print(f"  ✅ E-Mail gefunden (nach UPN-Filter): {email}")
            else:
                print(f"  ❌ Keine gültige E-Mail gefunden")
        else:
            print(f"  ❌ Keine E-Mail gefunden")
    
    print(f"\n📝 Nächste Schritte:")
    print(f"   1. Microsoft OAuth testen")
    print(f"   2. Backend-Logs für echte User-Info prüfen")
    print(f"   3. E-Mail-Extraktion debuggen")

if __name__ == "__main__":
    asyncio.run(test_microsoft_user_info()) 