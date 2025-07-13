#!/usr/bin/env python3
"""
Fix Admin Consent - Setzt DSGVO-Einwilligungen für Admin-Benutzer
"""

import asyncio
import sys
import os
from datetime import datetime

# Füge das app-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import get_db
from app.services.user_service import get_user_by_email

async def fix_admin_consent():
    """Setzt DSGVO-Einwilligungen für Admin-Benutzer"""
    print("🔧 Fixe Admin DSGVO-Einwilligungen...")
    
    try:
        # Hole Datenbankverbindung
        async for db in get_db():
            # Finde Admin-Benutzer
            admin_user = await get_user_by_email(db, 'admin@buildwise.de')
            
            if not admin_user:
                print("❌ Admin-Benutzer nicht gefunden!")
                return False
            
            print(f"✅ Admin-Benutzer gefunden: {admin_user.email}")
            print(f"📊 Aktuelle Einwilligungen:")
            print(f"   - Datenverarbeitung: {admin_user.data_processing_consent}")
            print(f"   - Marketing: {admin_user.marketing_consent}")
            print(f"   - Datenschutz: {admin_user.privacy_policy_accepted}")
            print(f"   - AGB: {admin_user.terms_accepted}")
            
            # Setze alle Einwilligungen auf True
            admin_user.data_processing_consent = True
            admin_user.marketing_consent = True
            admin_user.privacy_policy_accepted = True
            admin_user.terms_accepted = True
            admin_user.updated_at = datetime.utcnow()
            
            # Speichere Änderungen
            await db.commit()
            
            print("✅ DSGVO-Einwilligungen erfolgreich gesetzt!")
            print(f"📊 Neue Einwilligungen:")
            print(f"   - Datenverarbeitung: {admin_user.data_processing_consent}")
            print(f"   - Marketing: {admin_user.marketing_consent}")
            print(f"   - Datenschutz: {admin_user.privacy_policy_accepted}")
            print(f"   - AGB: {admin_user.terms_accepted}")
            
            return True
            
    except Exception as e:
        print(f"❌ Fehler beim Setzen der Einwilligungen: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(fix_admin_consent())
    if success:
        print("✅ Admin-Einwilligungen erfolgreich behoben!")
    else:
        print("❌ Fehler beim Beheben der Admin-Einwilligungen!")
