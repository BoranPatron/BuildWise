#!/usr/bin/env python3
"""
Einfaches Skript zum Neustarten des BuildWise Backends
"""

import subprocess
import sys
import os
import time

def restart_backend():
    print("🔄 Starte BuildWise Backend neu...")
    
    # Wechsle zum BuildWise-Verzeichnis
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    try:
        # Starte den Server
        cmd = [
            sys.executable, '-m', 'uvicorn',
            'app.main:app',
            '--host', '0.0.0.0',
            '--port', '8000',
            '--reload',
            '--log-level', 'info'
        ]
        
        print(f"🚀 Starte mit: {' '.join(cmd)}")
        print("🌐 Server wird verfügbar sein unter: http://localhost:8000")
        print("📚 API-Dokumentation: http://localhost:8000/docs")
        print("⏹️  Drücken Sie Ctrl+C zum Beenden")
        print("-" * 50)
        
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n⏹️  Server wird beendet...")
    except Exception as e:
        print(f"❌ Fehler beim Starten: {e}")
        return False
    
    return True

if __name__ == "__main__":
    restart_backend() 