#!/usr/bin/env python3
"""
Setup-Skript für Render.com Datenbank
Erstellt die Datenbank-Tabellen und fügt Test-Daten hinzu
"""

import asyncio
import os
import sys
from pathlib import Path

# Füge das Projektverzeichnis zum Python-Pfad hinzu
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.database import get_database_url
from app.models.base import Base
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.models.document import Document
from app.models.message import Message
from app.models.milestone import Milestone
from app.models.quote import Quote
from app.models.cost_position import CostPosition
from app.core.security import get_password_hash

async def setup_database():
    """Erstelle die Datenbank und Tabellen"""
    print("🚀 Starte Datenbank-Setup für Render.com...")
    
    # Hole die Datenbank-URL
    database_url = get_database_url()
    print(f"📊 Verwende Datenbank: {database_url}")
    
    # Erstelle Engine
    engine = create_async_engine(database_url, echo=True)
    
    try:
        # Erstelle alle Tabellen
        async with engine.begin() as conn:
            print("🔧 Erstelle Datenbank-Tabellen...")
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Tabellen erfolgreich erstellt")
        
        # Füge Test-Daten hinzu
        async with engine.begin() as conn:
            print("👤 Erstelle Test-Benutzer...")
            
            # Prüfe ob Admin-User bereits existiert
            result = await conn.execute(text("SELECT COUNT(*) FROM users WHERE email = 'admin@buildwise.de'"))
            count = result.scalar()
            
            if count == 0:
                # Erstelle Admin-User
                hashed_password = get_password_hash("admin123")
                await conn.execute(text("""
                    INSERT INTO users (
                        email, hashed_password, first_name, last_name, 
                        user_type, status, is_active, is_verified,
                        data_processing_consent, marketing_consent,
                        privacy_policy_accepted, terms_accepted
                    ) VALUES (
                        'admin@buildwise.de', :password, 'Admin', 'User',
                        'admin', 'active', 1, 1,
                        1, 1, 1, 1
                    )
                """), {"password": hashed_password})
                
                # Erstelle Dienstleister-User
                service_provider_password = get_password_hash("test1234")
                await conn.execute(text("""
                    INSERT INTO users (
                        email, hashed_password, first_name, last_name, 
                        user_type, status, is_active, is_verified,
                        data_processing_consent, marketing_consent,
                        privacy_policy_accepted, terms_accepted,
                        company_name, company_phone, company_website
                    ) VALUES (
                        'test-dienstleister@buildwise.de', :password, 'Test', 'Dienstleister',
                        'service_provider', 'active', 1, 1,
                        1, 1, 1, 1,
                        'Test GmbH', '+49 123 456789', 'https://test-gmbh.de'
                    )
                """), {"password": service_provider_password})
                
                print("✅ Test-Benutzer erstellt")
            else:
                print("ℹ️ Admin-User existiert bereits")
        
        print("🎉 Datenbank-Setup erfolgreich abgeschlossen!")
        
    except Exception as e:
        print(f"❌ Fehler beim Datenbank-Setup: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(setup_database()) 