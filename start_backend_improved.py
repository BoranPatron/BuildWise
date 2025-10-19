#!/usr/bin/env python3
"""
Verbessertes Backend-Start-Skript für BuildWise
Behebt asyncio-Probleme und bietet graceful shutdown
"""

import os
import sys
import subprocess
import time
import signal
import requests
from pathlib import Path

class GracefulBackendStarter:
    def __init__(self):
        self.process = None
        self.shutdown_requested = False
        
    def signal_handler(self, signum, frame):
        """Signal Handler für graceful shutdown"""
        print(f"\n🛑 Signal {signum} empfangen - starte graceful shutdown...")
        self.shutdown_requested = True
        self.stop_server()
        
    def check_dependencies(self):
        """Überprüft ob alle notwendigen Abhängigkeiten installiert sind"""
        required_packages = [
            'fastapi',
            'uvicorn',
            'sqlalchemy',
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
            try:
                subprocess.run([sys.executable, "-m", "pip", "install"] + missing_packages, check=True)
                print("✅ Abhängigkeiten installiert")
            except subprocess.CalledProcessError:
                print("❌ Fehler beim Installieren der Abhängigkeiten")
                return False
        return True

    def check_database(self):
        """Überprüft ob die Datenbank existiert und funktioniert"""
        db_path = Path("buildwise.db")
        if not db_path.exists():
            print("⚠️  Datenbank nicht gefunden. Erstelle neue Datenbank...")
            return False
        return True

    def start_server(self):
        """Startet den FastAPI-Server mit verbesserter Konfiguration"""
        print("🚀 Starte BuildWise Backend...")
        
        # Überprüfe ob wir im richtigen Verzeichnis sind
        if not Path("app/main.py").exists():
            print("❌ app/main.py nicht gefunden!")
            print("💡 Stelle sicher, dass du im BuildWise-Hauptverzeichnis bist")
            return False
        
        # Starte den Server mit verbesserter Konfiguration
        try:
            cmd = [
                sys.executable, "-m", "uvicorn",
                "app.main:app",
                "--reload",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--loop", "asyncio",  # Explizit asyncio loop verwenden
                "--timeout-keep-alive", "5",  # Kürzere Keep-Alive Zeit
                "--timeout-graceful-shutdown", "10"  # Graceful shutdown timeout
            ]
            
            print(f"🔧 Starte mit: {' '.join(cmd)}")
            
            # Starte Prozess ohne sofortiges Warten
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Server-Start fehlgeschlagen: {e}")
            return False

    def stop_server(self):
        """Stoppt den Server graceful"""
        if self.process:
            print("🛑 Stoppe Server...")
            try:
                # Erst SIGTERM senden (graceful)
                self.process.terminate()
                
                # Warte auf graceful shutdown
                try:
                    self.process.wait(timeout=10)
                    print("✅ Server graceful gestoppt")
                except subprocess.TimeoutExpired:
                    print("⚠️  Graceful shutdown timeout - force kill")
                    self.process.kill()
                    self.process.wait()
                    print("✅ Server force gestoppt")
                    
            except Exception as e:
                print(f"❌ Fehler beim Stoppen des Servers: {e}")

    def check_server_health(self, timeout=30):
        """Überprüft ob der Server erfolgreich gestartet ist"""
        print("⏳ Warte auf Server-Start...")
        start_time = time.time()
        
        while time.time() - start_time < timeout and not self.shutdown_requested:
            try:
                response = requests.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200:
                    print("✅ Server läuft erfolgreich auf http://localhost:8000")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
        
        if self.shutdown_requested:
            print("🛑 Shutdown während Health-Check angefordert")
            return False
        
        print("⚠️  Server-Health-Check fehlgeschlagen")
        return False

    def monitor_server(self):
        """Überwacht den Server-Prozess"""
        if not self.process:
            return
            
        try:
            # Lese Server-Output
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    print(f"[SERVER] {line.strip()}")
                    
                # Prüfe ob Prozess noch läuft
                if self.process.poll() is not None:
                    print("⚠️  Server-Prozess beendet")
                    break
                    
                # Prüfe auf Shutdown-Request
                if self.shutdown_requested:
                    break
                    
        except Exception as e:
            print(f"❌ Fehler beim Überwachen des Servers: {e}")

    def run(self):
        """Hauptfunktion mit verbesserter Fehlerbehandlung"""
        print("🏗️  BuildWise Backend - Verbesserter Start")
        print("=" * 50)
        
        # Signal Handler registrieren
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # 1. Abhängigkeiten prüfen
            print("📦 Prüfe Abhängigkeiten...")
            if not self.check_dependencies():
                print("❌ Abhängigkeiten konnten nicht installiert werden")
                return 1
            
            # 2. Datenbank prüfen
            print("🗄️  Prüfe Datenbank...")
            if not self.check_database():
                print("⚠️  Datenbank-Probleme erkannt")
            
            # 3. Server starten
            print("🚀 Starte Server...")
            if not self.start_server():
                print("❌ Server-Start fehlgeschlagen")
                return 1
            
            # 4. Health Check
            if not self.check_server_health():
                print("❌ Server konnte nicht gestartet werden")
                self.stop_server()
                return 1
            
            print("✅ Server erfolgreich gestartet!")
            print("🌐 Backend: http://localhost:8000")
            print("📚 API Docs: http://localhost:8000/docs")
            print("💡 Drücke Ctrl+C zum Beenden")
            
            # 5. Server überwachen
            self.monitor_server()
            
            return 0
            
        except KeyboardInterrupt:
            print("\n👋 KeyboardInterrupt empfangen")
            return 0
        except Exception as e:
            print(f"❌ Unerwarteter Fehler: {e}")
            return 1
        finally:
            self.stop_server()
            print("👋 BuildWise Backend beendet")

def main():
    """Hauptfunktion"""
    starter = GracefulBackendStarter()
    return starter.run()

if __name__ == "__main__":
    sys.exit(main())

