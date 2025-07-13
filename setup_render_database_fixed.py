#!/usr/bin/env python3
"""
Verbessertes Setup-Skript für Render.com Datenbank
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
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

async def setup_database():
    """Setup der Datenbank auf Render.com"""
    print("🚀 Starte Datenbank-Setup für Render.com...")
    
    # Hole die Datenbank-URL
    database_url = get_database_url()
    print(f"📊 Datenbank-URL: {database_url}")
    
    # Erstelle Engine
    engine = create_async_engine(database_url, echo=False)
    
    try:
        # Teste Verbindung
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ Datenbankverbindung erfolgreich")
        
        # Erstelle alle Tabellen
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Alle Tabellen erstellt")
        
        # Erstelle synchronen Engine für Daten-Insertion
        sync_database_url = database_url.replace("+aiosqlite", "")
        sync_engine = create_engine(sync_database_url, echo=False)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
        
        # Erstelle Test-Daten
        with SessionLocal() as db:
            # Prüfe ob Admin-User bereits existiert
            admin_user = db.query(User).filter(User.email == "admin@buildwise.de").first()
            if not admin_user:
                # Erstelle Admin-User
                admin_user = User(
                    email="admin@buildwise.de",
                    hashed_password=get_password_hash("admin123"),
                    first_name="Admin",
                    last_name="BuildWise",
                    user_type="professional",  # Enum-konform
                    is_active=True,
                    is_verified=True
                )
                db.add(admin_user)
                print("✅ Admin-User erstellt")
            else:
                print("ℹ️ Admin-User bereits vorhanden")
            
            # Prüfe ob Service-Provider existiert
            service_provider = db.query(User).filter(User.email == "test-dienstleister@buildwise.de").first()
            if not service_provider:
                # Erstelle Service-Provider
                service_provider = User(
                    email="test-dienstleister@buildwise.de",
                    hashed_password=get_password_hash("test1234"),
                    first_name="Test",
                    last_name="Dienstleister",
                    user_type="service_provider",  # Enum-konform
                    is_active=True,
                    is_verified=True
                )
                db.add(service_provider)
                print("✅ Service-Provider erstellt")
            else:
                print("ℹ️ Service-Provider bereits vorhanden")
            
            # Prüfe ob Test-Projekt existiert
            test_project = db.query(Project).filter(Project.name == "Test-Projekt").first()
            if not test_project:
                # Erstelle Test-Projekt
                test_project = Project(
                    name="Test-Projekt",
                    description="Ein Test-Projekt für BuildWise",
                    project_type="residential",
                    status="active",
                    budget=100000,
                    is_public=True,
                    allow_quotes=True,
                    owner_id=admin_user.id
                )
                db.add(test_project)
                print("✅ Test-Projekt erstellt")
            else:
                print("ℹ️ Test-Projekt bereits vorhanden")
            
            # Commit alle Änderungen
            db.commit()
            print("✅ Alle Test-Daten gespeichert")
        
        print("🎉 Datenbank-Setup erfolgreich abgeschlossen!")
        
    except Exception as e:
        print(f"❌ Fehler beim Datenbank-Setup: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(setup_database()) 