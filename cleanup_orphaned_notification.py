#!/usr/bin/env python3
"""
Skript zur Bereinigung der spezifischen verwaisten Benachrichtigung
Löscht die Benachrichtigung mit related_milestone_id: 2
"""

import asyncio
import sys
import os

# Füge den app-Ordner zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import get_db
from app.models.notification import Notification
from sqlalchemy import select, update

async def main():
    """Hauptfunktion zur Bereinigung der verwaisten Benachrichtigung"""
    print("🧹 Starte Bereinigung der verwaisten Benachrichtigung...")
    
    try:
        # Hole eine Datenbankverbindung
        async for db in get_db():
            # Finde die verwaiste Benachrichtigung mit related_milestone_id: 2
            result = await db.execute(
                select(Notification).where(Notification.related_milestone_id == 2)
            )
            orphaned_notifications = result.scalars().all()
            
            if not orphaned_notifications:
                print("✨ Keine verwaisten Benachrichtigungen mit related_milestone_id: 2 gefunden")
                return
            
            print(f"🔍 Gefunden: {len(orphaned_notifications)} verwaiste Benachrichtigung(en)")
            
            # Markiere alle verwaisten Benachrichtigungen als gelesen und quittiert
            for notification in orphaned_notifications:
                print(f"🗑️ Bereinige Benachrichtigung ID: {notification.id}")
                print(f"   - Typ: {notification.type}")
                print(f"   - Titel: {notification.title}")
                print(f"   - related_milestone_id: {notification.related_milestone_id}")
                
                # Markiere als gelesen und quittiert
                notification.is_read = True
                notification.is_acknowledged = True
                notification.read_at = "2024-01-01T00:00:00"  # Setze ein Datum
                notification.acknowledged_at = "2024-01-01T00:00:00"
            
            # Speichere Änderungen
            await db.commit()
            print(f"✅ {len(orphaned_notifications)} verwaiste Benachrichtigung(en) erfolgreich bereinigt")
            
            break  # Nur eine Iteration der Generator-Funktion
    
    except Exception as e:
        print(f"❌ Fehler bei der Bereinigung: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
