#!/usr/bin/env python3
"""
Automatisches Database Reset Skript für BuildWise
Erstellt eine jungfräuliche Datenbank ohne Benutzerabfrage.

Verwendung:
    python reset_database_auto.py                    # Standard Reset mit Admin
    python reset_database_auto.py --no-admin         # Ohne Admin-User
    python reset_database_auto.py --clean-storage    # Mit Storage-Bereinigung
    python reset_database_auto.py --full-reset       # Alles zurücksetzen
"""

import os
import sys
import asyncio
import argparse
from typing import Optional
from pathlib import Path


def get_script_dir() -> Path:
    """Gibt das Verzeichnis des Skripts zurück."""
    return Path(__file__).parent.absolute()


def print_banner():
    """Zeigt einen schönen Banner."""
    print("=" * 60)
    print("🔄 BuildWise Database Auto-Reset")
    print("=" * 60)


async def clear_database_data(seed_admin: bool = True) -> None:
    """
    Löscht alle Daten aus der Datenbank, behält aber die Struktur bei:
    - Prüft ob buildwise.db existiert
    - Löscht alle Daten aus allen Tabellen (TRUNCATE-ähnlich)
    - Behält Tabellen-Struktur, Indizes, Constraints bei
    - Optional: Seed minimaler Admin-User
    """
    script_dir = get_script_dir()
    db_path = script_dir / "buildwise.db"

    print(f"📍 Arbeitsverzeichnis: {script_dir}")
    print(f"🎯 Datenbank-Pfad: {db_path}")

    # 1) Prüfen ob DB existiert
    if not db_path.exists():
        print(f"❌ Datenbank nicht gefunden: {db_path}")
        print("💡 Erstelle neue Datenbank mit Struktur...")
        await create_fresh_database()
        if seed_admin:
            await seed_minimal_admin()
        return

    # 2) Daten aus allen Tabellen löschen (Struktur beibehalten)
    try:
        from app.core.database import engine, optimize_sqlite_connection
        from app.models import Base  # noqa: F401 - import needed to register models

        print("🧹 Lösche alle Daten (Struktur bleibt erhalten)...")
        
        async with engine.begin() as conn:
            # Alle Tabellen-Namen ermitteln
            from sqlalchemy import text
            tables_result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            )
            tables = [row[0] for row in tables_result.fetchall()]
            
            if not tables:
                print("ℹ️  Keine Tabellen gefunden - erstelle Struktur...")
                await conn.run_sync(Base.metadata.create_all)
                print("✅ Tabellen-Struktur erstellt")
            else:
                # Foreign Key Constraints temporär deaktivieren
                await conn.execute(text("PRAGMA foreign_keys = OFF"))
                
                # Alle Tabellen leeren
                deleted_count = 0
                for table in tables:
                    try:
                        result = await conn.execute(text(f"DELETE FROM {table}"))
                        count = result.rowcount or 0
                        deleted_count += count
                        if count > 0:
                            print(f"   🗑️  {table}: {count} Einträge gelöscht")
                    except Exception as e:
                        print(f"   ⚠️  Fehler bei Tabelle {table}: {e}")
                
                # Foreign Key Constraints wieder aktivieren
                await conn.execute(text("PRAGMA foreign_keys = ON"))
                
                # SQLite-spezifische Bereinigung
                await conn.execute(text("VACUUM"))
                
                print(f"✅ Insgesamt {deleted_count} Einträge aus {len(tables)} Tabellen gelöscht")

        # 3) SQLite-Optimierungen anwenden
        try:
            await optimize_sqlite_connection()
            print("⚡ SQLite-Optimierungen angewendet")
        except Exception as e:
            print(f"⚠️  SQLite-Optimierungen fehlgeschlagen: {e}")

    except ImportError as e:
        print(f"❌ Konnte App-Module nicht importieren: {e}")
        print("💡 Stelle sicher, dass du im BuildWise-Verzeichnis bist")
        raise
    except Exception as e:
        print(f"❌ Fehler beim Leeren der Datenbank: {e}")
        raise

    # 4) Optional: Admin-User anlegen
    if seed_admin:
        await seed_minimal_admin()


async def create_fresh_database() -> None:
    """Erstellt eine neue Datenbank mit vollständiger Struktur."""
    try:
        from app.core.database import engine, optimize_sqlite_connection
        from app.models import Base  # noqa: F401 - import needed to register models

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Neue Datenbank mit vollständiger Struktur erstellt")

        # SQLite-Optimierungen anwenden
        try:
            await optimize_sqlite_connection()
            print("⚡ SQLite-Optimierungen angewendet")
        except Exception as e:
            print(f"⚠️  SQLite-Optimierungen fehlgeschlagen: {e}")

    except Exception as e:
        print(f"❌ Fehler beim Erstellen der neuen Datenbank: {e}")
        raise


async def recreate_database_structure(seed_admin: bool = True) -> None:
    """
    Erstellt die Datenbank komplett neu (löscht auch die Struktur):
    - Löscht ./buildwise.db komplett
    - Erstellt Tabellen neu über SQLAlchemy
    - Optional: Seed minimaler Admin-User
    """
    script_dir = get_script_dir()
    db_path = script_dir / "buildwise.db"

    print(f"📍 Arbeitsverzeichnis: {script_dir}")
    print(f"🎯 Datenbank-Pfad: {db_path}")

    # 1) DB-Datei komplett löschen
    try:
        if db_path.exists():
            db_path.unlink()
            print(f"🧹 Datenbank komplett gelöscht: {db_path.name}")
        else:
            print(f"ℹ️  Keine bestehende Datenbank gefunden")
    except Exception as e:
        print(f"❌ Konnte Datenbank nicht löschen: {e}")
        raise

    # 2) Neue Datenbank mit Struktur erstellen
    await create_fresh_database()

    # 3) Optional: Admin-User anlegen
    if seed_admin:
        await seed_minimal_admin()


async def seed_minimal_admin() -> None:
    """Legt einen minimalen Admin-Benutzer an."""
    try:
        from sqlalchemy import select
        from app.core.database import AsyncSessionLocal
        from app.models import User
        from app.core.security import get_password_hash

        async with AsyncSessionLocal() as session:
            # Prüfe, ob bereits ein Admin existiert
            result = await session.execute(
                select(User).where(User.email == "admin@buildwise.local")
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print("ℹ️  Admin-User existiert bereits")
                return

            # Erstelle neuen Admin
            admin = User(
                email="admin@buildwise.local",
                first_name="System",
                last_name="Admin",
                user_type="developer",
                user_role="BAUTRAEGER",
                is_active=True,
            )
            admin.hashed_password = get_password_hash("Admin123!ChangeMe")

            session.add(admin)
            await session.commit()
            print("👤 Admin-User erstellt:")
            print("   📧 E-Mail: admin@buildwise.local")
            print("   🔑 Passwort: Admin123!ChangeMe")
            print("   ⚠️  Bitte Passwort nach dem ersten Login ändern!")

    except Exception as e:
        print(f"❌ Fehler beim Erstellen des Admin-Users: {e}")
        # Nicht kritisch - Datenbank ist trotzdem verwendbar
        print("💡 Datenbank ist trotzdem einsatzbereit")


def cleanup_storage(storage_path: Optional[Path] = None) -> None:
    """
    Bereinigt das Storage-Verzeichnis.
    Entfernt alle Dateien und Unterordner, behält aber das Hauptverzeichnis.
    """
    if storage_path is None:
        storage_path = get_script_dir() / "storage"

    if not storage_path.exists():
        print(f"ℹ️  Kein Storage-Verzeichnis gefunden: {storage_path}")
        return

    if not storage_path.is_dir():
        print(f"⚠️  Storage-Pfad ist kein Verzeichnis: {storage_path}")
        return

    removed_files = 0
    removed_dirs = 0

    try:
        # Alle Dateien und Unterordner entfernen
        for item in storage_path.rglob("*"):
            try:
                if item.is_file():
                    item.unlink()
                    removed_files += 1
                elif item.is_dir() and item != storage_path:
                    # Versuche leere Ordner zu entfernen
                    try:
                        item.rmdir()
                        removed_dirs += 1
                    except OSError:
                        # Ordner nicht leer - ignorieren
                        pass
            except Exception as e:
                print(f"⚠️  Konnte nicht entfernen {item}: {e}")

        print(f"🧹 Storage bereinigt:")
        print(f"   📄 Dateien entfernt: {removed_files}")
        print(f"   📁 Ordner entfernt: {removed_dirs}")

    except Exception as e:
        print(f"❌ Fehler beim Bereinigen des Storage: {e}")


def create_backup(db_path: Path) -> Optional[Path]:
    """Erstellt ein Backup der bestehenden Datenbank."""
    if not db_path.exists():
        return None

    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"buildwise_backup_{timestamp}.db"
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"💾 Backup erstellt: {backup_path.name}")
        return backup_path
    except Exception as e:
        print(f"⚠️  Backup fehlgeschlagen: {e}")
        return None


async def main():
    """Hauptfunktion mit Argument-Parsing."""
    parser = argparse.ArgumentParser(
        description="BuildWise Database Auto-Reset Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python reset_database_auto.py                    # Standard: Daten löschen, Struktur behalten
  python reset_database_auto.py --no-admin         # Ohne Admin-User
  python reset_database_auto.py --clean-storage    # Mit Storage-Bereinigung
  python reset_database_auto.py --full-reset       # Vollständiger Reset (Daten + Storage)
  python reset_database_auto.py --recreate-structure # Struktur komplett neu erstellen
  python reset_database_auto.py --backup           # Mit Backup
        """
    )
    
    parser.add_argument(
        "--no-admin", 
        action="store_true", 
        help="Keinen Admin-User erstellen"
    )
    parser.add_argument(
        "--clean-storage", 
        action="store_true", 
        help="Storage-Verzeichnis bereinigen"
    )
    parser.add_argument(
        "--full-reset", 
        action="store_true", 
        help="Vollständiger Reset (DB + Storage)"
    )
    parser.add_argument(
        "--recreate-structure", 
        action="store_true", 
        help="Datenbank komplett neu erstellen (löscht auch Struktur)"
    )
    parser.add_argument(
        "--backup", 
        action="store_true", 
        help="Backup der bestehenden DB erstellen"
    )
    parser.add_argument(
        "--quiet", "-q", 
        action="store_true", 
        help="Weniger Ausgaben"
    )

    args = parser.parse_args()

    # Banner anzeigen (außer im quiet mode)
    if not args.quiet:
        print_banner()

    # Arbeitsverzeichnis prüfen
    script_dir = get_script_dir()
    db_path = script_dir / "buildwise.db"
    
    if not (script_dir / "app").exists():
        print("❌ Fehler: Nicht im BuildWise-Verzeichnis!")
        print(f"   Aktuell: {script_dir}")
        print("   Erwartet: Verzeichnis mit 'app' Ordner")
        sys.exit(1)

    try:
        # Backup erstellen wenn gewünscht
        if args.backup:
            create_backup(db_path)

        # Storage bereinigen wenn gewünscht
        if args.clean_storage or args.full_reset:
            cleanup_storage()

        # Datenbank zurücksetzen
        seed_admin = not args.no_admin
        
        if args.recreate_structure:
            print("⚠️  Struktur wird komplett neu erstellt...")
            await recreate_database_structure(seed_admin=seed_admin)
        else:
            # Standard: Nur Daten löschen, Struktur beibehalten
            await clear_database_data(seed_admin=seed_admin)

        # Erfolgsmeldung
        if not args.quiet:
            print("=" * 60)
            print("🎉 BuildWise Datenbank erfolgreich zurückgesetzt!")
            print("=" * 60)
            if seed_admin:
                print("👤 Admin-Login: admin@buildwise.local / Admin123!ChangeMe")
            print("🚀 Die Anwendung kann jetzt gestartet werden.")

    except KeyboardInterrupt:
        print("\n⚠️  Abgebrochen durch Benutzer")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        if not args.quiet:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Direkt ausführen ohne Bestätigung
    asyncio.run(main())
