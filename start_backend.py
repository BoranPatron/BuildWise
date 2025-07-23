#!/usr/bin/env python3
"""
Skript zum Starten des BuildWise Backends
"""

import subprocess
import sys
import os

def start_backend():
    """Startet das Backend"""
    try:
        print("🚀 Starte BuildWise Backend...")
        print("📡 Backend wird auf http://localhost:8000 gestartet")
        print("💡 Drücke Ctrl+C zum Beenden")
        
        # Starte uvicorn
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ]
        
        subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
        
    except KeyboardInterrupt:
        print("\n👋 Backend beendet")
    except Exception as e:
        print(f"❌ Fehler beim Starten des Backends: {e}")

if __name__ == "__main__":
    start_backend() 