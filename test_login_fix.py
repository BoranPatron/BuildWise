#!/usr/bin/env python3
"""
Test-Script für Login nach Datenbank-Reparatur
"""

import asyncio
import sys
import os
import requests
import json

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.user import User
from app.core.security import verify_password
from sqlalchemy import select


async def test_database_connection():
    """Testet die Datenbankverbindung und User-Abfrage"""
    async for db in get_db():
        try:
            print("🔍 Teste Datenbankverbindung...")
            
            # Teste User-Abfrage
            result = await db.execute(select(User).where(User.email == "admin@buildwise.de"))
            admin_user = result.scalar_one_or_none()
            
            if admin_user:
                print(f"✅ Admin-User gefunden: {admin_user.email}")
                print(f"   ID: {admin_user.id}")
                print(f"   Status: {admin_user.status}")
                print(f"   E-Mail verifiziert: {admin_user.email_verified}")
                print(f"   DSGVO-Einwilligung: {admin_user.data_processing_consent}")
                print(f"   Subscription aktiv: {admin_user.subscription_active}")
                
                # Teste Passwort
                test_password = "Admin123!"
                if verify_password(test_password, admin_user.hashed_password):
                    print("✅ Passwort ist korrekt")
                else:
                    print("❌ Passwort ist falsch")
                
                return True
            else:
                print("❌ Admin-User nicht gefunden")
                return False
                
        except Exception as e:
            print(f"❌ Datenbankfehler: {e}")
            return False
        finally:
            await db.close()


def test_api_login():
    """Testet den API-Login"""
    try:
        print("\n🌐 Teste API-Login...")
        
        # Login-Daten
        login_data = {
            "username": "admin@buildwise.de",
            "password": "Admin123!"
        }
        
        # Sende Login-Request
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login erfolgreich!")
            print(f"   Token: {data.get('access_token', '')[:20]}...")
            print(f"   User: {data.get('user', {}).get('email', '')}")
            return True
        else:
            print(f"❌ Login fehlgeschlagen: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API-Fehler: {e}")
        return False


async def main():
    """Hauptfunktion"""
    print("🧪 Teste Login-Reparatur...")
    
    # Teste Datenbank
    db_ok = await test_database_connection()
    
    if db_ok:
        # Teste API
        api_ok = test_api_login()
        
        if api_ok:
            print("\n🎉 Login-Reparatur erfolgreich!")
            print("   Der Admin-Login sollte jetzt funktionieren.")
        else:
            print("\n⚠️ API-Login fehlgeschlagen")
            print("   Überprüfe Server-Logs für Details.")
    else:
        print("\n❌ Datenbank-Test fehlgeschlagen")


if __name__ == "__main__":
    asyncio.run(main()) 