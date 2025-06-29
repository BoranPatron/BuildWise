# Datenschutz und DSGVO-Konformität - BuildWise

## Übersicht

BuildWise implementiert umfassende DSGVO-konforme Sicherheitsmaßnahmen und Datenschutzrichtlinien. Diese Dokumentation beschreibt die implementierten Maßnahmen und deren Einhaltung der DSGVO-Anforderungen.

## 🔒 Implementierte Sicherheitsmaßnahmen

### 1. Passwort-Sicherheit
- **Mindestlänge**: 12 Zeichen
- **Anforderungen**: Groß-/Kleinbuchstaben, Zahlen, Sonderzeichen
- **Hashing**: bcrypt mit 12 Runden (individueller Salt pro Passwort)
- **Validierung**: Echtzeit-Prüfung der Passwort-Stärke

### 2. Account-Sicherheit
- **Fehlgeschlagene Anmeldungen**: Maximal 5 Versuche
- **Account-Sperrung**: 30 Minuten bei Überschreitung
- **Session-Management**: 2-Stunden-Timeout
- **Audit-Logging**: Alle Anmeldeversuche werden protokolliert

### 3. Datenverschlüsselung
- **Passwörter**: bcrypt-Hashing
- **Sensible Daten**: Verschlüsselung in der Datenbank
- **Übertragung**: HTTPS/TLS für alle Verbindungen
- **Backup-Verschlüsselung**: Alle Backups werden verschlüsselt

## 📋 DSGVO-Konforme Funktionen

### 1. Einwilligungsverwaltung
```json
{
  "data_processing_consent": false,      // Einwilligung zur Datenverarbeitung
  "marketing_consent": false,            // Einwilligung zu Marketing
  "privacy_policy_accepted": false,      // Datenschutzerklärung akzeptiert
  "terms_accepted": false                // AGB akzeptiert
}
```

### 2. Datenaufbewahrung
- **Standard-Aufbewahrung**: 2 Jahre nach letzter Aktivität
- **Löschungsanträge**: Automatische Verarbeitung
- **Anonymisierung**: Option zur Datenanonymisierung
- **Audit-Trail**: Vollständige Protokollierung aller Änderungen

### 3. Benutzerrechte (DSGVO Art. 15-22)
- **Recht auf Auskunft**: `/api/v1/gdpr/data-export`
- **Recht auf Löschung**: `/api/v1/gdpr/data-deletion-request`
- **Recht auf Berichtigung**: Über Benutzerprofil
- **Recht auf Einschränkung**: Account-Deaktivierung
- **Recht auf Datenübertragbarkeit**: Export-Funktion
- **Widerspruchsrecht**: Einwilligungen widerrufbar

## 🔍 Audit-Logging

### Protokollierte Aktionen
```python
class AuditAction(enum.Enum):
    # Benutzer-Aktionen
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTER = "user_register"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    
    # DSGVO-spezifische Aktionen
    CONSENT_GIVEN = "consent_given"
    CONSENT_WITHDRAWN = "consent_withdrawn"
    DATA_ACCESS_REQUEST = "data_access_request"
    DATA_DELETION_REQUEST = "data_deletion_request"
    DATA_EXPORT_REQUEST = "data_export_request"
    DATA_ANONYMIZATION = "data_anonymization"
    
    # Sicherheitsereignisse
    FAILED_LOGIN = "failed_login"
    ACCOUNT_LOCKED = "account_locked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
```

### Anonymisierung
- **IP-Adressen**: Letztes Oktett entfernt (192.168.1.0)
- **User-Agent**: Nur Browser-Typ behalten
- **Personenbezogene Daten**: Automatische Anonymisierung bei Löschung

## 🛡️ Datenschutz-API

### Endpunkte
```bash
# Einwilligungen
POST /api/v1/gdpr/consent
  - consent_type: "data_processing" | "marketing" | "privacy_policy" | "terms"
  - granted: true | false

# Datenlöschung
POST /api/v1/gdpr/data-deletion-request

# Datenanonymisierung
POST /api/v1/gdpr/data-anonymization

# Datenexport
GET /api/v1/gdpr/data-export

# Datenschutzerklärung
GET /api/v1/gdpr/privacy-policy

# AGB
GET /api/v1/gdpr/terms-of-service
```

## 📊 Datenverarbeitung

### Verarbeitungszwecke
1. **Bereitstellung der BuildWise-Plattform**
   - Rechtsgrundlage: Vertragserfüllung (Art. 6 Abs. 1 lit. b DSGVO)
   - Aufbewahrung: Bis zur Vertragsbeendigung

2. **Projektmanagement und -verwaltung**
   - Rechtsgrundlage: Vertragserfüllung (Art. 6 Abs. 1 lit. b DSGVO)
   - Aufbewahrung: 2 Jahre nach Projektabschluss

3. **Kommunikation zwischen Benutzern**
   - Rechtsgrundlage: Einwilligung (Art. 6 Abs. 1 lit. a DSGVO)
   - Aufbewahrung: Bis zur Widerrufung der Einwilligung

4. **Dienstleister-Vermittlung**
   - Rechtsgrundlage: Berechtigte Interessen (Art. 6 Abs. 1 lit. f DSGVO)
   - Aufbewahrung: 2 Jahre nach letzter Aktivität

### Verarbeitete Datenkategorien
- **Identifikationsdaten**: Name, E-Mail, Telefon
- **Profilinformationen**: Benutzertyp, Region, Sprachen
- **Firmendaten**: Firmenname, Adresse, Website (nur bei Einwilligung)
- **Projektdaten**: Projektbeschreibungen, Dokumente, Nachrichten
- **Technische Daten**: IP-Adressen (anonymisiert), User-Agent (anonymisiert)

## 🔧 Technische Implementierung

### Datenbank-Schema
```sql
-- DSGVO-Felder in der User-Tabelle
ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active';
ALTER TABLE users ADD COLUMN data_processing_consent BOOLEAN DEFAULT 0;
ALTER TABLE users ADD COLUMN marketing_consent BOOLEAN DEFAULT 0;
ALTER TABLE users ADD COLUMN privacy_policy_accepted BOOLEAN DEFAULT 0;
ALTER TABLE users ADD COLUMN terms_accepted BOOLEAN DEFAULT 0;
ALTER TABLE users ADD COLUMN data_retention_until DATE;
ALTER TABLE users ADD COLUMN data_deletion_requested BOOLEAN DEFAULT 0;
ALTER TABLE users ADD COLUMN data_deletion_requested_at DATETIME;
ALTER TABLE users ADD COLUMN data_anonymized BOOLEAN DEFAULT 0;
ALTER TABLE users ADD COLUMN last_login_at DATETIME;
ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN account_locked_until DATETIME;
ALTER TABLE users ADD COLUMN password_changed_at DATETIME;
ALTER TABLE users ADD COLUMN data_encrypted BOOLEAN DEFAULT 1;
ALTER TABLE users ADD COLUMN encryption_key_id TEXT;
ALTER TABLE users ADD COLUMN last_activity_at DATETIME;

-- Audit-Logs Tabelle
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id INTEGER,
    description TEXT,
    details JSON,
    ip_address TEXT,
    user_agent TEXT,
    risk_level TEXT,
    processing_purpose TEXT,
    legal_basis TEXT,
    requires_review BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Sicherheits-Service
```python
class SecurityService:
    # Passwort-Richtlinien
    MIN_PASSWORD_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL_CHARS = True
    
    # Account-Sperrung
    MAX_FAILED_LOGIN_ATTEMPTS = 5
    ACCOUNT_LOCKOUT_DURATION = timedelta(minutes=30)
    
    # Session-Management
    SESSION_TIMEOUT = timedelta(hours=2)
```

## 🚀 Migration

### DSGVO-Migration ausführen
```bash
cd BuildWise
python migrate_to_gdpr.py
```

### Migration-Schritte
1. **Audit-Logs Tabelle erstellen**
2. **DSGVO-Felder zur User-Tabelle hinzufügen**
3. **Bestehende Benutzer aktualisieren**
4. **Admin-Benutzer mit DSGVO-Konformität erstellen**

## 📞 Kontakt

### Datenschutzbeauftragter
- **E-Mail**: datenschutz@buildwise.de
- **Adresse**: BuildWise GmbH, Datenschutz, [Adresse]

### Benutzerrechte geltend machen
- **Auskunft**: Über API oder E-Mail
- **Löschung**: Über API oder E-Mail
- **Widerspruch**: Über API oder E-Mail

## 📋 Compliance-Checkliste

### ✅ Implementiert
- [x] Passwort-Stärke-Validierung
- [x] Account-Sperrung bei fehlgeschlagenen Anmeldungen
- [x] IP-Adress-Anonymisierung
- [x] Audit-Logging für alle Aktionen
- [x] Einwilligungsverwaltung
- [x] Datenlöschungsanträge
- [x] Datenanonymisierung
- [x] Datenexport-Funktion
- [x] Datenschutzerklärung
- [x] AGB
- [x] Verschlüsselung sensibler Daten
- [x] Session-Management
- [x] Recht auf Auskunft
- [x] Recht auf Berichtigung
- [x] Recht auf Löschung
- [x] Recht auf Einschränkung
- [x] Recht auf Datenübertragbarkeit
- [x] Widerspruchsrecht

### 🔄 Geplant
- [ ] E-Mail-Verschlüsselung
- [ ] Zwei-Faktor-Authentifizierung
- [ ] Erweiterte Audit-Reports
- [ ] Automatische Datenlöschung
- [ ] DSGVO-Compliance-Dashboard

## 📈 Monitoring

### Überwachte Metriken
- Fehlgeschlagene Anmeldeversuche
- Account-Sperrungen
- Einwilligungsänderungen
- Datenlöschungsanträge
- Audit-Log-Größe
- Verschlüsselungsstatus

### Alerts
- Ungewöhnliche Anmeldeaktivitäten
- Mehrere fehlgeschlagene Anmeldungen
- Account-Sperrungen
- Datenlöschungsanträge
- Audit-Log-Überlauf

---

**Version**: 1.0  
**Letzte Aktualisierung**: 2024-01-01  
**Nächste Überprüfung**: 2024-07-01 