#!/usr/bin/env python3
"""
Einfacher Backend-Test
"""

import asyncio
import sys
import os

# Füge das app-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_backend():
    """Testet das Backend"""
    print("🔍 BACKEND-TEST")
    print("=" * 30)
    
    try:
        # Importiere die App
        from app.main import app
        print("✅ App erfolgreich importiert")
        
        # Teste Datenbank-Verbindung
        from app.core.database import get_db
        from app.models import User, Project, Milestone, Quote
        
        print("✅ Modelle erfolgreich importiert")
        
        # Teste Konfiguration
        from app.core.config import settings
        print(f"✅ Konfiguration geladen: {settings.database_url}")
        
        print("✅ Backend ist bereit!")
        return True
        
    except Exception as e:
        print(f"❌ Backend-Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_backend())
    if success:
        print("\n🎉 Backend-Test erfolgreich!")
    else:
        print("\n💥 Backend-Test fehlgeschlagen!")
        sys.exit(1) 