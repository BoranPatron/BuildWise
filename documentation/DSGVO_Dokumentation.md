# DSGVO-Dokumentation für BuildWise

## Übersicht

BuildWise ist eine DSGVO-konforme Plattform für Immobilienprojekte. Diese Dokumentation beschreibt alle implementierten Datenschutz- und Sicherheitsmaßnahmen.

## 🔒 Implementierte Sicherheitsmaßnahmen

### 1. Passwort-Sicherheit

#### Passwort-Stärke-Validierung
- **Mindestlänge**: 12 Zeichen
- **Anforderungen**:
  - Mindestens ein Großbuchstabe
  - Mindestens ein Kleinbuchstabe
  - Mindestens eine Zahl
  - Mindestens ein Sonderzeichen
- **Häufige Passwörter**: Werden blockiert
- **Hashing**: bcrypt mit 12 Runden (hohe Sicherheit)

#### Account-Sperrung
- **Maximale fehlgeschlagene Anmeldungen**: 5 Versuche
- **Sperrdauer**: 30 Minuten
- **Automatische Entsperrung**: Nach Ablauf der Sperrzeit

### 2. Datenanonymisierung

#### IP-Adress-Anonymisierung
- **IPv4**: Letztes Oktett wird entfernt (192.168.1.123 → 192.168.1.0)
- **IPv6**: Letzte 64 Bits werden entfernt
- **Zweck**: DSGVO-konforme Protokollierung

#### User-Agent-Anonymisierung
- **Browser-Erkennung**: Nur Browser-Typ wird gespeichert
- **Persönliche Daten**: Werden entfernt
- **Beispiel**: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124" → "Chrome Browser"

### 3. Audit-Logging

#### Protokollierte Aktionen
- **Benutzer-Aktionen**: Login, Logout, Registrierung, Profiländerungen
- **DSGVO-Aktionen**: Einwilligungen, Datenlöschung, Datenexport
- **Sicherheitsereignisse**: Fehlgeschlagene Anmeldungen, Account-Sperrungen
- **Datenzugriff**: CRUD-Operationen auf alle Ressourcen

#### Audit-Log-Felder
```sql
- user_id: Wer hat die Aktion ausgeführt
- session_id: Session-ID für anonyme Aktionen
- ip_address: Anonymisierte IP-Adresse
- user_agent: Anonymisierter User-Agent
- action: Art der Aktion (AuditAction Enum)
- resource_type: Betroffene Ressource
- resource_id: ID der Ressource
- description: Beschreibung der Aktion
- details: Zusätzliche Details (verschlüsselt)
- processing_purpose: Zweck der Datenverarbeitung
- legal_basis: Rechtsgrundlage
- risk_level: Risikobewertung (low/medium/high)
- created_at: Zeitstempel
```

### 4. DSGVO-konforme Benutzerverwaltung

#### Einwilligungsverwaltung
- **Datenverarbeitung**: Einwilligung zur Datenverarbeitung
- **Marketing**: Einwilligung zu Marketing-E-Mails
- **Datenschutzerklärung**: Akzeptierung der Datenschutzerklärung
- **AGB**: Akzeptierung der Allgemeinen Geschäftsbedingungen

#### Datenaufbewahrung
- **Aufbewahrungsfrist**: Konfigurierbar pro Benutzer
- **Standard**: 2 Jahre nach Registrierung
- **Löschungsantrag**: Benutzer können Löschung beantragen
- **Anonymisierung**: Alternative zur vollständigen Löschung

#### Benutzerstatus
- **ACTIVE**: Aktiver Benutzer
- **INACTIVE**: Inaktiver Benutzer
- **SUSPENDED**: Gesperrter Benutzer
- **DELETED**: Gelöschter Benutzer

## 📋 DSGVO-API-Endpunkte

### Einwilligungsverwaltung
```http
POST /api/v1/gdpr/consent
{
  "consent_type": "data_processing|marketing|privacy_policy|terms",
  "granted": true|false
}
```

### Datenlöschung
```http
POST /api/v1/gdpr/data-deletion-request
```

### Datenanonymisierung
```http
POST /api/v1/gdpr/data-anonymization
```

### Datenexport
```http
GET /api/v1/gdpr/data-export
```

### Datenschutzerklärung
```http
GET /api/v1/gdpr/privacy-policy
```

### AGB
```http
GET /api/v1/gdpr/terms-of-service
```

## 🔐 Authentifizierung und Autorisierung

### JWT-Token-Management
- **Algorithmus**: HS256
- **Ablaufzeit**: 30 Minuten (konfigurierbar)
- **Refresh-Token**: Verfügbar für Token-Erneuerung
- **Sichere Speicherung**: Nur im Memory des Browsers

### Rollen und Berechtigungen
- **PRIVATE**: Privatnutzer (Bauherren)
- **PROFESSIONAL**: Professionelle Nutzer (Architekten, Planer)
- **SERVICE_PROVIDER**: Dienstleister (Handwerker, Bauträger)

## 📊 Datenverarbeitung

### Zweckbindung
Alle Datenverarbeitungen sind zweckgebunden:
- **Projektmanagement**: Verwaltung von Bauprojekten
- **Dienstleister-Vermittlung**: Matching von Bauherren und Dienstleistern
- **Kommunikation**: In-App-Kommunikation zwischen Nutzern
- **Support**: Kundenservice und technischer Support

### Rechtsgrundlagen
- **Einwilligung**: Für Marketing und optionale Datenverarbeitung
- **Vertragserfüllung**: Für Kernfunktionen der Plattform
- **Berechtigtes Interesse**: Für Sicherheitsmaßnahmen und Betrugsbekämpfung

### Datenminimierung
- **Zweckgebundene Erhebung**: Nur notwendige Daten werden erhoben
- **Anonymisierung**: Wo möglich werden Daten anonymisiert
- **Pseudonymisierung**: Persönliche Daten werden pseudonymisiert

## 🛡️ Technische Sicherheitsmaßnahmen

### Verschlüsselung
- **Datenbank**: Alle sensiblen Daten sind verschlüsselt
- **Übertragung**: HTTPS/TLS für alle API-Kommunikation
- **Passwörter**: bcrypt-Hashing mit individuellem Salt

### Zugriffskontrolle
- **Authentifizierung**: JWT-basierte Authentifizierung
- **Autorisierung**: Rollenbasierte Zugriffskontrolle
- **Session-Management**: Sichere Session-Verwaltung

### Netzwerksicherheit
- **CORS**: Konfigurierte Cross-Origin Resource Sharing
- **Rate-Limiting**: Schutz vor Brute-Force-Angriffen
- **Input-Validierung**: Schutz vor Injection-Angriffen

## 📈 Monitoring und Compliance

### Audit-Trail
- **Vollständige Protokollierung**: Alle Benutzeraktionen werden protokolliert
- **Risikobewertung**: Automatische Risikobewertung von Aktionen
- **Manuelle Überprüfung**: Hochrisiko-Aktionen werden zur manuellen Überprüfung markiert

### Compliance-Reporting
- **Datenexport**: Benutzer können ihre Daten exportieren
- **Löschungsanträge**: Automatisierte Bearbeitung von Löschungsanträgen
- **Einwilligungsverwaltung**: Transparente Verwaltung aller Einwilligungen

### Incident-Response
- **Automatische Erkennung**: Verdächtige Aktivitäten werden automatisch erkannt
- **Account-Sperrung**: Automatische Sperrung bei verdächtigen Aktivitäten
- **Benachrichtigung**: Benachrichtigung bei Sicherheitsvorfällen

## 🔄 Datenlebenszyklus

### 1. Datenerhebung
- **Einwilligung**: Explizite Einwilligung vor Datenerhebung
- **Zweckbindung**: Klare Angabe des Verarbeitungszwecks
- **Minimierung**: Nur notwendige Daten werden erhoben

### 2. Datenverarbeitung
- **Sicherheit**: Verschlüsselte Verarbeitung
- **Zugriffskontrolle**: Rollenbasierte Zugriffskontrolle
- **Protokollierung**: Vollständige Audit-Trails

### 3. Datenaufbewahrung
- **Zeitliche Begrenzung**: Konfigurierbare Aufbewahrungsfristen
- **Zweckbindung**: Daten werden nur für den ursprünglichen Zweck aufbewahrt
- **Sicherheit**: Verschlüsselte Speicherung

### 4. Datenlöschung
- **Automatische Löschung**: Nach Ablauf der Aufbewahrungsfrist
- **Löschungsanträge**: Bearbeitung von Benutzeranfragen
- **Anonymisierung**: Alternative zur vollständigen Löschung

## 📞 Kontakt und Support

### Datenschutzbeauftragter
- **E-Mail**: datenschutz@buildwise.de
- **Telefon**: +49 (0) 123 456789
- **Adresse**: BuildWise GmbH, Datenschutz, Musterstraße 123, 12345 Musterstadt

### Benutzerrechte
Benutzer haben folgende Rechte:
- **Auskunftsrecht**: Recht auf Auskunft über verarbeitete Daten
- **Berichtigungsrecht**: Recht auf Berichtigung falscher Daten
- **Löschungsrecht**: Recht auf Löschung der Daten
- **Einschränkungsrecht**: Recht auf Einschränkung der Verarbeitung
- **Datenübertragbarkeit**: Recht auf Datenübertragbarkeit
- **Widerspruchsrecht**: Recht auf Widerspruch gegen die Verarbeitung

### Beschwerderecht
Benutzer haben das Recht, sich bei der zuständigen Aufsichtsbehörde zu beschweren:
- **Bundesbeauftragter für den Datenschutz und die Informationsfreiheit**
- **Landesdatenschutzbeauftragte** der jeweiligen Bundesländer

## 📋 Compliance-Checkliste

### ✅ Implementierte Maßnahmen
- [x] DSGVO-konforme Benutzerregistrierung
- [x] Einwilligungsverwaltung
- [x] Datenminimierung
- [x] Zweckbindung
- [x] Verschlüsselung sensibler Daten
- [x] Audit-Logging
- [x] Datenlöschungsanträge
- [x] Datenexport
- [x] Anonymisierung
- [x] Passwort-Sicherheit
- [x] Account-Sperrung
- [x] IP-Adress-Anonymisierung
- [x] Rollenbasierte Zugriffskontrolle
- [x] Session-Management
- [x] Input-Validierung
- [x] CORS-Konfiguration

### 🔄 Regelmäßige Überprüfungen
- [ ] Monatliche Sicherheitsaudits
- [ ] Quartalsweise Compliance-Reviews
- [ ] Jährliche DSGVO-Assessments
- [ ] Kontinuierliche Sicherheitsupdates

## 🚀 Nächste Schritte

### Kurzfristig (1-3 Monate)
1. **Penetrationstests**: Externe Sicherheitsaudits
2. **Datenschutz-Folgenabschätzung**: Für neue Features
3. **Schulungen**: Mitarbeiter-Schulungen zu DSGVO

### Mittelfristig (3-12 Monate)
1. **Zertifizierung**: ISO 27001 Zertifizierung
2. **Erweiterte Verschlüsselung**: End-to-End-Verschlüsselung
3. **KI-basierte Bedrohungserkennung**: Erweiterte Sicherheitsmaßnahmen

### Langfristig (1+ Jahre)
1. **Zero-Trust-Architektur**: Erweiterte Sicherheitsarchitektur
2. **Blockchain-Integration**: Für Audit-Trails
3. **Internationale Compliance**: Erweiterung auf andere Rechtsräume

---

**Dokument erstellt**: 2024-01-01  
**Letzte Aktualisierung**: 2024-01-01  
**Version**: 1.0  
**Verantwortlich**: BuildWise Datenschutz-Team 