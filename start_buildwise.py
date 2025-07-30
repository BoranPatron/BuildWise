#!/usr/bin/env python3
"""
Nachhaltiges BuildWise Start-Skript
Startet Backend und Frontend mit automatischer Fehlerbehandlung
"""

import os
import sys
import subprocess
import time
import threading
import requests
from pathlib import Path

class BuildWiseStarter:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.backend_running = False
        self.frontend_running = False
        
    def check_backend_health(self):
        """Überprüft Backend-Health in einem separaten Thread"""
        while True:
            try:
                response = requests.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200 and not self.backend_running:
                    print("✅ Backend läuft erfolgreich")
                    self.backend_running = True
                elif response.status_code != 200 and self.backend_running:
                    print("⚠️  Backend nicht erreichbar")
                    self.backend_running = False
            except requests.exceptions.RequestException:
                if self.backend_running:
                    print("⚠️  Backend nicht erreichbar")
                    self.backend_running = False
            time.sleep(5)
    
    def start_backend(self):
        """Startet das Backend"""
        print("🚀 Starte BuildWise Backend...")
        
        # Überprüfe ob wir im richtigen Verzeichnis sind
        if not Path("app/main.py").exists():
            print("❌ app/main.py nicht gefunden!")
            print("💡 Stelle sicher, dass du im BuildWise-Hauptverzeichnis bist")
            return False
        
        try:
            cmd = [
                sys.executable, "-m", "uvicorn",
                "app.main:app",
                "--reload",
                "--host", "0.0.0.0",
                "--port", "8000"
            ]
            
            print(f"🔧 Backend-Start: {' '.join(cmd)}")
            self.backend_process = subprocess.Popen(cmd)
            return True
            
        except Exception as e:
            print(f"❌ Backend-Start fehlgeschlagen: {e}")
            return False
    
    def start_frontend(self):
        """Startet das Frontend"""
        print("🎨 Starte BuildWise Frontend...")
        
        frontend_dir = Path("Frontend/Frontend")
        if not frontend_dir.exists():
            print("❌ Frontend-Verzeichnis nicht gefunden!")
            return False
        
        try:
            cmd = ["npm", "run", "dev"]
            print(f"🔧 Frontend-Start: {' '.join(cmd)}")
            self.frontend_process = subprocess.Popen(cmd, cwd=frontend_dir)
            return True
            
        except Exception as e:
            print(f"❌ Frontend-Start fehlgeschlagen: {e}")
            return False
    
    def wait_for_backend(self, timeout=30):
        """Wartet bis das Backend verfügbar ist"""
        print("⏳ Warte auf Backend...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200:
                    print("✅ Backend ist bereit!")
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        
        print("⚠️  Backend-Timeout erreicht")
        return False
    
    def start_services(self):
        """Startet beide Services"""
        print("🏗️  BuildWise - Nachhaltiger Start")
        print("=" * 50)
        
        # 1. Backend starten
        if not self.start_backend():
            return False
        
        # 2. Warten auf Backend
        if not self.wait_for_backend():
            print("❌ Backend konnte nicht gestartet werden")
            return False
        
        # 3. Frontend starten
        if not self.start_frontend():
            print("❌ Frontend konnte nicht gestartet werden")
            return False
        
        print("✅ Beide Services gestartet!")
        print("🌐 Backend: http://localhost:8000")
        print("🎨 Frontend: http://localhost:5173")
        print("💡 Drücke Ctrl+C zum Beenden")
        
        return True
    
    def stop_services(self):
        """Stoppt beide Services"""
        print("\n👋 Stoppe Services...")
        
        if self.frontend_process:
            self.frontend_process.terminate()
            print("✅ Frontend gestoppt")
        
        if self.backend_process:
            self.backend_process.terminate()
            print("✅ Backend gestoppt")
    
    def run(self):
        """Hauptfunktion"""
        try:
            # Starte Health-Check Thread
            health_thread = threading.Thread(target=self.check_backend_health, daemon=True)
            health_thread.start()
            
            # Starte Services
            if self.start_services():
                # Warte auf Benutzer-Interruption
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
            else:
                print("❌ Services konnten nicht gestartet werden")
                return 1
                
        except KeyboardInterrupt:
            print("\n👋 Beende BuildWise...")
        finally:
            self.stop_services()
        
        return 0

def main():
    """Hauptfunktion"""
    starter = BuildWiseStarter()
    return starter.run()

if __name__ == "__main__":
    sys.exit(main()) 