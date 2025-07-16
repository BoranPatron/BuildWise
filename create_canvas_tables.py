#!/usr/bin/env python3
"""
Skript zum Erstellen der Canvas-Tabellen in der Datenbank
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.database import engine
from app.models import Base
from app.models.canvas import Canvas, CanvasObject, CollaborationArea, CanvasSession

def create_canvas_tables():
    """Erstellt die Canvas-Tabellen in der Datenbank"""
    try:
        print("🔧 Erstelle Canvas-Tabellen...")
        
        # Erstelle alle Tabellen
        Base.metadata.create_all(bind=engine, tables=[
            Canvas.__table__,
            CanvasObject.__table__,
            CollaborationArea.__table__,
            CanvasSession.__table__
        ])
        
        print("✅ Canvas-Tabellen erfolgreich erstellt!")
        
        # Prüfe ob Tabellen existieren
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('canvases', 'canvas_objects', 'collaboration_areas', 'canvas_sessions')
            """))
            tables = [row[0] for row in result]
            
            print(f"📋 Erstellte Tabellen: {', '.join(tables)}")
            
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Canvas-Tabellen: {e}")
        return False
    
    return True

if __name__ == "__main__":
    create_canvas_tables() 