import asyncio
import sqlite3
from sqlalchemy import text
from app.core.database import engine

async def add_rejection_reason_column():
    """Fügt die rejection_reason Spalte zur quotes Tabelle hinzu"""
    try:
        # Verwende SQLite direkt für die Schema-Änderung
        conn = sqlite3.connect('buildwise.db')
        cursor = conn.cursor()
        
        # Prüfe ob die Spalte bereits existiert
        cursor.execute("PRAGMA table_info(quotes)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'rejection_reason' not in columns:
            cursor.execute("ALTER TABLE quotes ADD COLUMN rejection_reason TEXT")
            conn.commit()
            print("✅ rejection_reason Spalte erfolgreich hinzugefügt")
        else:
            print("ℹ️ rejection_reason Spalte existiert bereits")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Fehler beim Hinzufügen der Spalte: {e}")

if __name__ == "__main__":
    asyncio.run(add_rejection_reason_column()) 