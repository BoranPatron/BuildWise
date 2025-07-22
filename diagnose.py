#!/usr/bin/env python3
"""
System-Diagnose
"""

import sys
import os

def diagnose_system():
    """Diagnostiziert das System"""
    print("🔍 SYSTEM-DIAGNOSE")
    print("=" * 20)
    
    print(f"🐍 Python-Version: {sys.version}")
    print(f"📁 Arbeitsverzeichnis: {os.getcwd()}")
    print(f"📂 Python-Pfad: {sys.path}")
    
    # Teste SQLite
    try:
        import sqlite3
        print("✅ SQLite verfügbar")
    except ImportError as e:
        print(f"❌ SQLite-Fehler: {e}")
    
    # Teste FastAPI
    try:
        import fastapi
        print("✅ FastAPI verfügbar")
    except ImportError as e:
        print(f"❌ FastAPI-Fehler: {e}")
    
    # Teste SQLAlchemy
    try:
        import sqlalchemy
        print("✅ SQLAlchemy verfügbar")
    except ImportError as e:
        print(f"❌ SQLAlchemy-Fehler: {e}")
    
    # Prüfe Datenbank
    db_path = "buildwise.db"
    if os.path.exists(db_path):
        print(f"✅ Datenbank gefunden: {os.path.abspath(db_path)}")
        print(f"📊 Größe: {os.path.getsize(db_path)} Bytes")
    else:
        print(f"❌ Datenbank nicht gefunden: {db_path}")
    
    # Prüfe app-Verzeichnis
    app_path = "app"
    if os.path.exists(app_path):
        print(f"✅ App-Verzeichnis gefunden: {os.path.abspath(app_path)}")
        files = os.listdir(app_path)
        print(f"📁 Dateien: {len(files)}")
    else:
        print(f"❌ App-Verzeichnis nicht gefunden: {app_path}")

if __name__ == "__main__":
    diagnose_system() 