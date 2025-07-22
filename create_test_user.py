#!/usr/bin/env python3
"""
Skript zur Erstellung eines Test-Benutzers für API-Tests
"""

import asyncio
import sys
import os
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.user import User, UserType
from app.core.security import get_password_hash
from sqlalchemy import select

async def create_test_user():
    """Erstellt einen Test-Benutzer für API-Tests."""
    
    print("🔧 Erstelle Test-Benutzer...")
    
    try:
        async for db in get_db():
            # Prüfe, ob Test-Benutzer bereits existiert
            result = await db.execute(
                select(User).where(User.email == "test@buildwise.de")
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"✅ Test-Benutzer bereits vorhanden: {existing_user.email}")
                return existing_user
            
            # Erstelle neuen Test-Benutzer
            test_user = User(
                email="test@buildwise.de",
                hashed_password=get_password_hash("test123"),
                first_name="Test",
                last_name="User",
                user_type=UserType.PRIVATE,  # Verwende PRIVATE statt SERVICE_PROVIDER
                is_active=True,
                data_processing_consent=True,
                privacy_policy_accepted=True,
                terms_accepted=True
            )
            
            db.add(test_user)
            await db.commit()
            await db.refresh(test_user)
            
            print(f"✅ Test-Benutzer erstellt: {test_user.email}")
            print(f"   - ID: {test_user.id}")
            print(f"   - Name: {test_user.first_name} {test_user.last_name}")
            print(f"   - Type: {test_user.user_type}")
            print(f"   - Password: test123")
            
            return test_user
            
        except Exception as e:
        print(f"❌ Fehler beim Erstellen des Test-Benutzers: {e}")
            return None

if __name__ == "__main__":
    asyncio.run(create_test_user()) 