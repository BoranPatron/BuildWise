#!/usr/bin/env python3
"""
Test-Skript für Datei-Speicherung
"""

import asyncio
import aiofiles
from pathlib import Path

async def test_file_save():
    """Testet die Datei-Speicherung"""
    
    print("🔍 Test: Datei-Speicherung")
    
    try:
        # Simuliere save_uploaded_file
        project_id = 8
        filename = "test_file.txt"
        file_content = b"Test content for file saving"
        
        # Erstelle Projektordner
        upload_dir = Path(f"storage/uploads/project_{project_id}")
        print(f"📁 Upload-Verzeichnis: {upload_dir}")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generiere Dateipfad
        file_path = upload_dir / filename
        print(f"📄 Dateipfad: {file_path}")
        
        # Speichere Datei
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        print("✅ Datei erfolgreich gespeichert")
        
        # Prüfe ob Datei existiert
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✅ Datei existiert ({size} bytes)")
            
            # Lösche Test-Datei
            file_path.unlink()
            print("🗑️  Test-Datei gelöscht")
        else:
            print("❌ Datei wurde nicht erstellt")
            
    except ImportError as e:
        print(f"❌ Import-Fehler: {e}")
        print("💡 Möglicherweise ist aiofiles nicht installiert")
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    asyncio.run(test_file_save())