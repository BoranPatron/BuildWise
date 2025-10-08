import os
import asyncio
from typing import Optional


def confirm_or_exit() -> None:
    """
    Verhindert Ausführung ohne explizite Bestätigung.
    Setze RESET_CONFIRM=YES um das Skript auszuführen.
    """
    if os.getenv("RESET_CONFIRM", "NO").upper() != "YES":
        print("[ERROR] Sicherheitssperre aktiv. Setze RESET_CONFIRM=YES um fortzufahren.")
        raise SystemExit(1)


async def drop_and_recreate_db(seed_admin: bool = True) -> None:
    """
    - Beendet aktive Verbindungen (SQLite: nicht nötig, aber wir löschen die Datei vorsichtig)
    - Löscht ./buildwise.db wenn vorhanden
    - Erstellt Tabellen neu über SQLAlchemy Base.metadata.create_all
    - Optional: Seed minimaler Systemdaten (z. B. Admin-User)
    """
    # Pfad zur SQLite-Datei
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "buildwise.db"))

    # 1) DB-Datei löschen, wenn vorhanden
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"[CLEAN] Entfernt: {db_path}")
        else:
            print(f"[INFO] Keine bestehende DB gefunden unter: {db_path}")
    except Exception as e:
        print(f"[ERROR] Konnte DB-Datei nicht löschen: {e}")
        raise

    # 2) Tabellen neu erstellen über SQLAlchemy Base
    from app.core.database import engine, optimize_sqlite_connection
    from app.models import Base  # noqa: F401 - import needed to register models

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("[SUCCESS] Tabellen neu erstellt")

    # 3) SQLite-Optimierungen anwenden (optional, wie im App-Startup)
    try:
        await optimize_sqlite_connection()
    except Exception as e:
        print(f"[WARNING] SQLite-Optimierungen konnten nicht angewendet werden: {e}")

    # 4) Optionale System-Seeds (minimal)
    if seed_admin:
        await seed_minimal_admin()


async def seed_minimal_admin() -> None:
    """Lege einen minimalen Admin-Benutzer an, falls nicht vorhanden."""
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models import User  # type: ignore
    from app.core.security import get_password_hash  # nutzt euer Security-Modul

    async with AsyncSessionLocal() as session:
        # Prüfe, ob bereits ein Admin existiert
        result = await session.execute(select(User).where(User.email == "admin@buildwise.local"))
        existing = result.scalar_one_or_none()
        if existing:
            print("[INFO] Admin existiert bereits – Seed übersprungen")
            return

        admin = User(
            email="admin@buildwise.local",
            first_name="System",
            last_name="Admin",
            user_type="developer",  # oder passender interner Typ
            user_role="BAUTRAEGER",  # falls Rollenmodell aktiv ist
            is_active=True,
        )
        # Setze ein sicheres Default-Passwort (bitte unmittelbar nach dem Start ändern)
        admin.hashed_password = get_password_hash("Admin123!ChangeMe")

        session.add(admin)
        await session.commit()
        print("[SUCCESS] Minimaler Admin-User angelegt: admin@buildwise.local / Admin123!ChangeMe")


def maybe_cleanup_storage(remove_storage: bool = False) -> None:
    """
    Optional: Storage leeren. Standard: False, um Dateien nicht zu verlieren.
    Entfernt alles unter ./storage außer das Verzeichnis selbst.
    """
    if not remove_storage:
        print("[INFO] Storage bleibt unangetastet (REMOVE_STORAGE nicht gesetzt)")
        return

    storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "storage"))
    if not os.path.isdir(storage_dir):
        print(f"[INFO] Kein Storage-Verzeichnis gefunden unter: {storage_dir}")
        return

    removed = 0
    for root, dirs, files in os.walk(storage_dir, topdown=False):
        for name in files:
            try:
                fp = os.path.join(root, name)
                os.remove(fp)
                removed += 1
            except Exception as e:
                print(f"[WARNING] Konnte Datei nicht entfernen {fp}: {e}")
        for name in dirs:
            try:
                dp = os.path.join(root, name)
                # Leere Unterordner entfernen, root storage Ordner bleibt bestehen
                if dp != storage_dir:
                    os.rmdir(dp)
            except OSError:
                # Ordner nicht leer – ignorieren
                pass
    print(f"[CLEAN] Storage bereinigt – entfernte Dateien: {removed}")


if __name__ == "__main__":
    confirm_or_exit()

    remove_storage_flag = os.getenv("REMOVE_STORAGE", "NO").upper() == "YES"
    # 1) Optional Storage leeren
    maybe_cleanup_storage(remove_storage_flag)
    # 2) DB jungfräulich anlegen und minimal seeden
    asyncio.run(drop_and_recreate_db(seed_admin=True))
    print("[SUCCESS] buildwise.db wurde jungfräulich neu erstellt.")





