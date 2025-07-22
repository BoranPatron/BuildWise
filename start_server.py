#!/usr/bin/env python3
"""
BuildWise Server Start-Skript
Startet den FastAPI-Server mit Fehlerbehandlung
"""

import sys
import os
import subprocess
import time

def check_dependencies():
    """Prüft, ob alle erforderlichen Abhängigkeiten installiert sind"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'aiosqlite',
        'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} ist installiert")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} fehlt")
    
    if missing_packages:
        print(f"\n📦 Installiere fehlende Pakete: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
            print("✅ Alle Abhängigkeiten installiert")
        except subprocess.CalledProcessError as e:
            print(f"❌ Fehler beim Installieren der Abhängigkeiten: {e}")
            return False
    
    return True

def start_server():
    """Startet den FastAPI-Server"""
    print("🚀 Starte BuildWise Server...")
    
    # Prüfe Abhängigkeiten
    if not check_dependencies():
        print("❌ Server-Start fehlgeschlagen - Abhängigkeiten fehlen")
        return False
    
    # Server-Konfiguration
    host = "0.0.0.0"
    port = 8000
    reload = True
    
    print(f"🌐 Server wird gestartet auf http://{host}:{port}")
    print("📚 API-Dokumentation: http://localhost:8000/docs")
    print("🏥 Health Check: http://localhost:8000/health")
    print("⏹️  Drücken Sie Ctrl+C zum Beenden")
    print("-" * 50)
    
    try:
        # Starte den Server
        cmd = [
            sys.executable, '-m', 'uvicorn',
            'app.main:app',
            '--host', host,
            '--port', str(port),
            '--reload' if reload else '',
            '--log-level', 'info'
        ]
        
        # Entferne leere Strings
        cmd = [arg for arg in cmd if arg]
        
        print(f"🔧 Starte mit Kommando: {' '.join(cmd)}")
        
        # Starte den Server
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Server-Fehler: {e}")
        return False
    except KeyboardInterrupt:
        print("\n⏹️  Server wird beendet...")
        return True
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
        return False

if __name__ == "__main__":
    # Wechsle zum BuildWise-Verzeichnis
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("🏗️  BuildWise Server Starter")
    print("=" * 50)
    
    success = start_server()
    
    if success:
        print("✅ Server erfolgreich beendet")
    else:
        print("❌ Server-Start fehlgeschlagen")
        sys.exit(1) 