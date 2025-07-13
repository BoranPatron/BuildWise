#!/usr/bin/env python3
"""
Prüft, ob das Disk-Verzeichnis /var/data auf Render.com existiert und beschreibbar ist.
"""
import os
import sys

def check_disk(path="/var/data"):
    print(f"🔍 Prüfe Disk-Verzeichnis: {path}")
    if not os.path.exists(path):
        print(f"❌ Verzeichnis {path} existiert NICHT!")
        print("💡 Lösung: Stelle sicher, dass die Disk in Render.com gemountet ist und der Mount Path korrekt ist.")
        sys.exit(1)
    if not os.access(path, os.W_OK):
        print(f"❌ Verzeichnis {path} ist NICHT beschreibbar!")
        print("💡 Lösung: Prüfe die Disk-Konfiguration und Berechtigungen auf Render.com.")
        sys.exit(2)
    print(f"✅ Verzeichnis {path} existiert und ist beschreibbar.")
    # Test: Schreibe und lösche eine Testdatei
    testfile = os.path.join(path, "test_write_access.txt")
    try:
        with open(testfile, "w") as f:
            f.write("Test erfolgreich!")
        os.remove(testfile)
        print("✅ Schreibtest erfolgreich.")
    except Exception as e:
        print(f"❌ Fehler beim Schreiben in {path}: {e}")
        sys.exit(3)

if __name__ == "__main__":
    check_disk() 