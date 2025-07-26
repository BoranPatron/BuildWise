#!/usr/bin/env python3
"""
Skript um verfügbare Benutzer in der Datenbank zu prüfen
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models.user import User

def check_users():
    try:
        db = next(get_db())
        users = db.query(User).all()
        
        print("=== Verfügbare Benutzer ===")
        if not users:
            print("❌ Keine Benutzer in der Datenbank gefunden!")
            return
        
        for user in users:
            print(f"✅ {user.email} (ID: {user.id}, Role: {user.role})")
            
        print(f"\n=== Gesamt: {len(users)} Benutzer ===")
        
    except Exception as e:
        print(f"❌ Fehler beim Prüfen der Benutzer: {e}")

if __name__ == "__main__":
    check_users() 