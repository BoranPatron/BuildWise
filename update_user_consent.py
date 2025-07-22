#!/usr/bin/env python3
"""
Skript zum Aktualisieren der DSGVO-Einwilligungen eines Benutzers
"""

import asyncio
import sys
from pathlib import Path

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import update

async def update_user_consent():
    """Aktualisiert die DSGVO-Einwilligungen des Benutzers admin@buildwise.de"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Benutzer finden
            from sqlalchemy import select
            stmt = select(User).where(User.email == "admin@buildwise.de")
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                print("❌ Benutzer admin@buildwise.de nicht gefunden!")
                return None
            
            print(f"✅ Benutzer gefunden: {user.email}")
            print(f"📊 Aktuelle Einwilligungen:")
            print(f"   - Datenverarbeitung: {user.data_processing_consent}")
            print(f"   - Marketing: {user.marketing_consent}")
            print(f"   - Datenschutz: {user.privacy_policy_accepted}")
            print(f"   - AGB: {user.terms_accepted}")
            
            # Einwilligungen aktualisieren
            stmt = update(User).where(User.email == "admin@buildwise.de").values(
                data_processing_consent=True,
                marketing_consent=True,
                privacy_policy_accepted=True,
                terms_accepted=True
            )
            await db.execute(stmt)
            await db.commit()
            
            print(f"\n✅ Einwilligungen erfolgreich aktualisiert!")
            print(f"📊 Neue Einwilligungen:")
            print(f"   - Datenverarbeitung: True")
            print(f"   - Marketing: True")
            print(f"   - Datenschutz: True")
            print(f"   - AGB: True")
            
            return user
            
        except Exception as e:
            print(f"❌ Fehler beim Aktualisieren der Einwilligungen: {e}")
            return None

async def main():
    """Hauptfunktion"""
    print("🚀 Aktualisiere DSGVO-Einwilligungen für admin@buildwise.de...")
    
    user = await update_user_consent()
    
    if user:
        print("\n🎉 Einwilligungen aktualisiert! Du kannst dich jetzt einloggen mit:")
        print("   E-Mail: admin@buildwise.de")
        print("   Passwort: Admin123!")
    else:
        print("\n❌ Fehler beim Aktualisieren der Einwilligungen!")

if __name__ == "__main__":
    asyncio.run(main()) 