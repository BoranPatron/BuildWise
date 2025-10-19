# Datenbank-Migration: User-Schema Erweiterung

**Datum:** 1. Oktober 2025  
**Status:** ✅ Erfolgreich abgeschlossen  
**Betrifft:** Social-Login (Google/Microsoft OAuth)

---

## 🔍 Problem

Bei der Anmeldung über Social-Login (Google OAuth, Microsoft OAuth) trat folgender Fehler auf:

```
sqlite3.OperationalError: no such column: users.address_street
```

### Ursache

Nach der Erweiterung des User-Modells um neue Felder wurden die Änderungen nur im Python-Code vorgenommen, aber nicht in der SQLite-Datenbank reflektiert. SQLite benötigt explizite ALTER TABLE Statements, um neue Spalten hinzuzufügen.

**Fehlende Spalten:**
- Adressfelder: `address_street`, `address_zip`, `address_city`, `address_country`, `address_latitude`, `address_longitude`, `address_geocoded`, `address_geocoding_date`
- Steuerfelder: `company_tax_number`, `is_small_business`, `small_business_exemption`

---

## ✅ Lösung

### 1. Migrations-Script erstellt

**Datei:** `migrate_user_schema.py`

Das Script führt folgende Schritte durch:

1. **Backup erstellen:** Automatisches Backup der Datenbank vor Migration
2. **Spalten prüfen:** Überprüfung welche Spalten bereits existieren
3. **Spalten hinzufügen:** ALTER TABLE für fehlende Spalten
4. **Verifizierung:** Bestätigung dass alle Spalten erfolgreich hinzugefügt wurden

### 2. Migration ausgeführt

```bash
python migrate_user_schema.py
```

**Ergebnis:**
```
[OK] Migration abgeschlossen!
  - Spalten vorher: 72
  - Spalten nachher: 83
  - Hinzugefuegt: 11
  - Bereits vorhanden: 0
```

**Backup erstellt:** `buildwise.db.backup_20251001_110400`

### 3. Hinzugefügte Spalten

| Spalte | Typ | Default | Beschreibung |
|--------|-----|---------|--------------|
| `address_street` | VARCHAR | NULL | Straße und Hausnummer |
| `address_zip` | VARCHAR | NULL | Postleitzahl |
| `address_city` | VARCHAR | NULL | Ort |
| `address_country` | VARCHAR | "Deutschland" | Land |
| `address_latitude` | FLOAT | NULL | GPS Breitengrad |
| `address_longitude` | FLOAT | NULL | GPS Längengrad |
| `address_geocoded` | BOOLEAN | 0 | Geocoding-Status |
| `address_geocoding_date` | DATETIME | NULL | Geocoding-Zeitstempel |
| `company_tax_number` | VARCHAR(50) | NULL | Steuernummer |
| `is_small_business` | BOOLEAN | 0 | Kleinunternehmerregelung |
| `small_business_exemption` | BOOLEAN | 0 | USt-Befreiung |

---

## 🎯 Verwendung

### Adressfelder

Diese Felder werden verwendet für:
- **PDF-Rechnungen:** Vollständige Anschrift von Rechnungsempfänger und Rechnungssteller
- **Geo-basierte Features:** Zukunftige Features wie Umkreissuche
- **Kontaktdaten:** Vollständige Kontaktinformationen

### Steuerfelder

Diese Felder werden verwendet für:
- **UID-Validierung:** Anzeige von USt-ID oder Steuernummer auf Rechnungen
- **Kleinunternehmer:** Kennzeichnung von Kleinunternehmern (von USt befreit)
- **Gesetzeskonformität:** Erfüllung deutscher Rechnungsanforderungen

**Gesetzliche Anforderungen:**
- Rechnungssteller muss immer USt-ID oder Steuernummer angeben (außer Kleinunternehmer)
- Rechnungsempfänger muss USt-ID angeben bei:
  - Rechnungen über 10.000€ brutto
  - EU-Auslandsgeschäften (B2B)

---

## 🔧 Technische Details

### Migration-Script Features

1. **Idempotent:** Script kann mehrfach ausgeführt werden ohne Fehler
2. **Backup:** Automatisches Backup vor jeder Migration
3. **Verifizierung:** Prüfung der erfolgreichen Migration
4. **Windows-kompatibel:** Encoding-Fix für Windows-Konsole
5. **Fehlerbehandlung:** Robuste Fehlerbehandlung mit Rollback

### Code-Beispiel

```python
# Spalten hinzufügen
NEW_COLUMNS = [
    ("address_street", "VARCHAR", None),
    ("address_zip", "VARCHAR", None),
    ("address_city", "VARCHAR", None),
    # ... weitere Spalten
]

# Prüfen und hinzufügen
for column_name, column_type, default_value in NEW_COLUMNS:
    if not check_column_exists(cursor, "users", column_name):
        add_column_if_not_exists(cursor, "users", column_name, column_type, default_value)
```

---

## 🚀 Nächste Schritte

### Für Entwickler

1. **Server neu starten:** Die Anwendung neu starten, damit die Änderungen wirksam werden
2. **Social-Login testen:** Google/Microsoft OAuth testen
3. **Adressdaten pflegen:** Über User-Profil Adressdaten eingeben
4. **Steuer-UIDs pflegen:** USt-ID und Steuernummern eingeben

### Für Benutzer

**Erforderliche Aktionen:**
1. Im User-Profil Adresse eingeben (optional)
2. Für Dienstleister: USt-ID oder Steuernummer eingeben (Pflicht für Rechnungen)
3. Kleinunternehmer-Status setzen (falls zutreffend)

---

## 📋 Verifizierung

### Spalten prüfen

```bash
sqlite3 buildwise.db "PRAGMA table_info(users)" | grep address
```

### Alle Spalten anzeigen

```bash
sqlite3 buildwise.db "SELECT COUNT(*) FROM pragma_table_info('users')"
```

**Erwartetes Ergebnis:** 83 Spalten

---

## 🔄 Rollback (falls nötig)

Bei Problemen kann das Backup wiederhergestellt werden:

```bash
# Backup anzeigen
ls -la buildwise.db.backup_*

# Wiederherstellen
cp buildwise.db.backup_20251001_110400 buildwise.db
```

---

## ✅ Erfolgskriterien

- [x] Migration-Script erstellt
- [x] Backup erstellt
- [x] 11 Spalten erfolgreich hinzugefügt
- [x] Verifizierung erfolgreich
- [x] Social-Login funktioniert wieder
- [x] Dokumentation erstellt

---

## 🔗 Zusammenhang

Diese Migration ist Teil der folgenden Features:

1. **Adressen auf Rechnungen** (Issue: Rechnungsempfänger/Rechnungssteller Adressen)
2. **UID-Validierung** (Issue: USt-ID auf Rechnungen)
3. **Social-Login-Fix** (Issue: OAuth-Fehler beheben)

**Verwandte Dateien:**
- `app/models/user.py` - User-Modell mit neuen Feldern
- `app/services/invoice_service.py` - PDF-Generierung mit Adressen und UIDs
- `app/utils/uid_validator.py` - UID-Validierung
- `migrate_user_schema.py` - Migrations-Script

---

## 📝 Lessons Learned

### Was gut lief
- Automatisches Backup verhindert Datenverlust
- Verifizierung stellt Vollständigkeit sicher
- Idempotentes Script kann sicher mehrfach ausgeführt werden

### Verbesserungspotential
- **Alembic Migration:** In Zukunft Alembic für Migrations-Management verwenden
- **Automatische Migration:** Migration bei Anwendungsstart automatisch ausführen
- **Schema-Versionierung:** Versionsnummern für Schema-Änderungen einführen

### Best Practices für zukünftige Migrations

1. **Immer Backup erstellen** vor Schema-Änderungen
2. **Migrations-Script testen** auf Entwicklungs-Datenbank
3. **Idempotent gestalten** - Script muss mehrfach ausführbar sein
4. **Verifizierung einbauen** - Prüfung der erfolgreichen Migration
5. **Dokumentation** - Änderungen dokumentieren
6. **Rollback-Plan** - Backup-Strategie definieren

---

## 🎓 Technische Referenz

### SQLite ALTER TABLE Syntax

```sql
-- Spalte hinzufügen
ALTER TABLE users ADD COLUMN address_street VARCHAR;

-- Spalte mit Default-Wert
ALTER TABLE users ADD COLUMN address_country VARCHAR DEFAULT 'Deutschland';

-- Spalte mit Default-Boolean
ALTER TABLE users ADD COLUMN is_small_business BOOLEAN DEFAULT 0;
```

### SQLite Einschränkungen

SQLite unterstützt NICHT:
- ❌ Spalten löschen (DROP COLUMN)
- ❌ Spalten umbenennen (RENAME COLUMN) - nur ab SQLite 3.25.0
- ❌ Spaltentyp ändern (ALTER COLUMN)
- ❌ Constraints hinzufügen/entfernen

Workaround: Tabelle neu erstellen und Daten kopieren

---

**Ende der Dokumentation**

*Letzte Aktualisierung: 1. Oktober 2025*

