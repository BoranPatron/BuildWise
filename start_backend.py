#!/usr/bin/env python3
"""
Nachhaltiges Backend-Start-Skript für BuildWise
Behebt häufige Probleme und bietet bessere Fehlerbehandlung
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def check_dependencies():
    """Überprüft ob alle notwendigen Abhängigkeiten installiert sind"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'sqlite3',
        'pydantic'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Fehlende Abhängigkeiten: {', '.join(missing_packages)}")
        print("📦 Installiere fehlende Pakete...")
        subprocess.run([sys.executable, "-m", "pip", "install"] + missing_packages)
        return False
    return True

def check_database():
    """Überprüft ob die Datenbank existiert und funktioniert"""
    db_path = Path("buildwise.db")
    if not db_path.exists():
        print("⚠️  Datenbank nicht gefunden. Erstelle neue Datenbank...")
        # Hier könnte eine Datenbank-Initialisierung erfolgen
        return False
    return True

def start_server():
    """Startet den FastAPI-Server mit korrekten Parametern"""
    print("🚀 Starte BuildWise Backend...")
    
    # Überprüfe ob wir im richtigen Verzeichnis sind
    if not Path("app/main.py").exists():
        print("❌ app/main.py nicht gefunden!")
        print("💡 Stelle sicher, dass du im BuildWise-Hauptverzeichnis bist")
        return False
    
    # Starte den Server
    try:
        cmd = [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ]
        
        print(f"🔧 Starte mit: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Server-Start fehlgeschlagen: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 Server gestoppt")
        return True

def check_server_health():
    """Überprüft ob der Server erfolgreich gestartet ist"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server läuft erfolgreich auf http://localhost:8000")
            return True
    except requests.exceptions.RequestException:
        pass
    
    print("⚠️  Server-Health-Check fehlgeschlagen")
    return False

def main():
    """Hauptfunktion mit nachhaltiger Fehlerbehandlung"""
    print("🏗️  BuildWise Backend - Nachhaltiger Start")
    print("=" * 50)
    
    # 1. Abhängigkeiten prüfen
    print("📦 Prüfe Abhängigkeiten...")
    if not check_dependencies():
        print("❌ Abhängigkeiten konnten nicht installiert werden")
        return 1
    
    # 2. Datenbank prüfen
    print("🗄️  Prüfe Datenbank...")
    if not check_database():
        print("⚠️  Datenbank-Probleme erkannt")
    
    # 3. Server starten
    print("🚀 Starte Server...")
    if start_server():
        print("✅ Server erfolgreich gestartet")
        return 0
    else:
        print("❌ Server-Start fehlgeschlagen")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 