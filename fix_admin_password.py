#!/usr/bin/env python3
"""
Skript zum Korrigieren des Admin-Passworts für BuildWise
Verwendung: python fix_admin_password.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Füge das app-Verzeichnis zum Python-Pfad hinzu
sys.path.append(str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal
from app.services.user_service import get_user_by_email
from app.services.security_service import SecurityService
from sqlalchemy import update
from app.models.user import User
from datetime import datetime, timezone

async def fix_admin_password():
    """Korrigiert das Admin-Passwort für admin@buildwise.de"""
    
    admin_email = "admin@buildwise.de"
    new_password = "admin123"  # Einfaches Passwort für den Zugang
    
    try:
        # Verwende AsyncSessionLocal für die Session-Verwaltung
        async with AsyncSessionLocal() as session:
            # Prüfen, ob Admin existiert
            existing_user = await get_user_by_email(session, admin_email)
            
            if not existing_user:
                print(f"❌ Admin-Account mit E-Mail {admin_email} existiert nicht!")
                print("   Erstellen Sie zuerst einen Admin-Account mit create_admin.py")
                return False
            
            print(f"✅ Admin-Account gefunden:")
            print(f"   Benutzer-ID: {existing_user.id}")
            print(f"   E-Mail: {existing_user.email}")
            print(f"   Name: {existing_user.first_name} {existing_user.last_name}")
            print(f"   Status: {existing_user.status}")
            print()
            
            # Neues Passwort hashen
            hashed_password = SecurityService.hash_password(new_password)
            
            # Passwort in der Datenbank aktualisieren
            await session.execute(
                update(User)
                .where(User.id == existing_user.id)
                .values(
                    hashed_password=hashed_password,
                    password_changed_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
            )
            
            # Änderungen committen
            await session.commit()
            
            print("✅ Admin-Passwort erfolgreich korrigiert!")
            print()
            print("🔑 Neue Login-Daten:")
            print(f"   E-Mail: {admin_email}")
            print(f"   Passwort: {new_password}")
            print()
            print("⚠️  WICHTIG: Ändern Sie das Passwort nach dem Login!")
            return True
        
    except Exception as e:
        print(f"❌ Fehler beim Korrigieren des Admin-Passworts: {e}")
        return False

async def main():
    """Hauptfunktion"""
    print("🔧 BuildWise Admin-Passwort Korrektur")
    print("=" * 50)
    
    success = await fix_admin_password()
    
    if success:
        print("✅ Admin-Passwort-Korrektur abgeschlossen!")
        print()
        print("📝 Nächste Schritte:")
        print("1. Starten Sie das Backend: python -m uvicorn app.main:app --reload")
        print("2. Starten Sie das Frontend: npm run dev")
        print("3. Melden Sie sich mit den neuen Admin-Daten an")
        print("4. Ändern Sie das Passwort nach dem Login")
    else:
        print("❌ Admin-Passwort-Korrektur fehlgeschlagen!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 