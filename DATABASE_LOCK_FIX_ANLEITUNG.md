# Database Lock Fix Anleitung 🔧

## Problem
```
❌ Global Exception Handler: OperationalError: (sqlite3.OperationalError) database is locked
```

## Ursache
SQLite-Datenbank ist gesperrt, weil mehrere Prozesse gleichzeitig darauf zugreifen.

## Lösung

### Option 1: Server neu starten (Empfohlen)
1. **Stoppe alle Python-Prozesse**:
   - `Ctrl + C` in allen Terminal-Fenstern
   - Oder schließe alle Terminal-Fenster

2. **Warte 5 Sekunden**

3. **Starte den Server neu**:
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Option 2: Database-Reset (Falls Option 1 nicht hilft)
1. **Stoppe alle Server**
2. **Führe Database-Reset aus**:
   ```bash
   python reset_database_connection.py
   ```
3. **Starte Server neu**

### Option 3: Manueller Database-Fix
1. **Öffne SQLite-Browser** oder **DB Browser for SQLite**
2. **Öffne**: `buildwise.db`
3. **Führe aus**:
   ```sql
   PRAGMA journal_mode=WAL;
   PRAGMA synchronous=NORMAL;
   PRAGMA cache_size=-64000;
   PRAGMA foreign_keys=ON;
   PRAGMA busy_timeout=30000;
   VACUUM;
   ANALYZE;
   ```

### Option 4: Database neu erstellen (Letzte Option)
1. **Backup erstellen**:
   ```bash
   copy buildwise.db buildwise_backup.db
   ```
2. **Database löschen**:
   ```bash
   del buildwise.db
   ```
3. **Server starten** (erstellt neue Database):
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Technische Details

### Was wurde bereits behoben:
- ✅ **Router-Fehler**: Doppelter Router entfernt
- ✅ **bcrypt-Fehler**: Fallback auf sha256_crypt
- ✅ **Database-Konfiguration**: Optimierte SQLite-Einstellungen

### Database-Optimierungen implementiert:
```python
SQLITE_CONFIG = {
    "check_same_thread": False,
    "timeout": 30.0,
    "isolation_level": None,
    "pragma": {
        "journal_mode": "WAL",
        "synchronous": "NORMAL",
        "cache_size": -64000,
        "foreign_keys": "ON",
        "busy_timeout": 30000
    }
}
```

## Status
🎯 **Router-Fix abgeschlossen - Database-Lock muss behoben werden**

Nach der Behebung des Database-Lock-Problems sollte die Anwendung vollständig funktionieren. 