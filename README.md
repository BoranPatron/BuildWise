# BuildWise - Digitaler Assistent für Immobilienprojekte

## Übersicht

BuildWise ist eine vollständige Backendlösung für eine digitale Plattform, die private Bauherren, Architekten, Bauträger, kleine Bauunternehmen sowie Handwerker und Planer verbindet. Die Plattform zielt darauf ab, den gesamten Bauprozess zu vereinfachen, zu optimieren und transparenter zu gestalten.

## 🚀 Funktionen

### 4.1 Modul: Projektmanagement (Kernfunktionen für Bauherren)

- **Geführter Projektablauf**: Schritt-für-Schritt-Führung durch alle Projektphasen
- **Dynamische Projektzeitleiste**: Interaktive, grafische Darstellung des Projektfortschritts
- **Dokumentenmanagement**: Zentrale, cloudbasierte Speicherung aller projektrelevanten Dokumente
- **Budget- und Kostenmanagement**: Erfassung und Verfolgung des Projektbudgets

### 4.2 Modul: Dienstleister-Vermittlung

- **Anonyme Angebotsanfrage**: Automatisches Matching mit passenden, regionalen Dienstleistern
- **KI-gestützter Angebotsvergleich**: Automatische Analyse eingegangener Angebote
- **Dienstleister-Profile**: Detaillierte Profile mit Leistungen, Referenzen und Qualifikationen
- **Kontaktfreigabe**: Erst nach Annahme eines Angebots werden Kontaktdaten freigegeben

### 4.3 Modul: Kommunikation & Support

- **In-App-Kommunikation**: Chat-Funktion für die Kommunikation zwischen Bauherren und Dienstleistern
- **KI-Chatbot**: Automatisierter Support für häufig gestellte Fragen
- **Benachrichtigungssystem**: Push-Benachrichtigungen und E-Mail-Benachrichtigungen

### 4.4 Modul: Benutzerverwaltung

- **Registrierung & Login**: Getrennte Registrierungsprozesse für Privatnutzer und Dienstleister
- **Profilverwaltung**: Möglichkeit für Nutzer, persönliche/Firmendaten zu bearbeiten
- **Sichere Authentifizierung**: JWT-basierte Authentifizierung mit optionaler 2FA

## 🛠 Technologie-Stack

- **Backend**: FastAPI (Python)
- **Datenbank**: PostgreSQL mit SQLAlchemy ORM
- **Authentifizierung**: JWT mit Passlib
- **Dokumentenverwaltung**: Lokale Dateispeicherung mit aiofiles
- **API-Dokumentation**: Automatische OpenAPI/Swagger-Dokumentation
- **Tests**: pytest mit async Support
- **Code-Qualität**: black, flake8, mypy

## 📋 Voraussetzungen

- Python 3.8+
- PostgreSQL 12+
- Redis (für zukünftige Caching-Funktionen)

## 🚀 Installation

### 1. Repository klonen
```bash
git clone <repository-url>
cd BuildWise
```

### 2. Virtuelle Umgebung erstellen
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# oder
.venv\Scripts\activate  # Windows
```

### 3. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```

### 4. Umgebungsvariablen konfigurieren
Erstellen Sie eine `.env` Datei im Hauptverzeichnis:

```env
# Datenbank
DB_HOST=localhost
DB_PORT=5432
DB_NAME=buildwise
DB_USER=postgres
DB_PASSWORD=your_password

# JWT
JWT_SECRET_KEY=your_secret_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Optional: E-Mail (für zukünftige Funktionen)
SENDGRID_API_KEY=your_sendgrid_key
FROM_EMAIL=noreply@buildwise.com
```

### 5. Datenbank einrichten
```bash
# PostgreSQL-Datenbank erstellen
createdb buildwise

# Migrationen ausführen (falls vorhanden)
alembic upgrade head
```

### 6. Anwendung starten
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 API-Dokumentation

Nach dem Start der Anwendung ist die API-Dokumentation verfügbar unter:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🗄 Datenbank-Schema

### Hauptentitäten

#### Users
- Verschiedene Benutzertypen (PRIVATE, PROFESSIONAL, SERVICE_PROVIDER)
- Erweiterte Profilinformationen für Dienstleister
- E-Mail-Verifizierung und 2FA-Support

#### Projects
- Vollständige Projektverwaltung mit Status-Tracking
- Budget- und Kostenverfolgung
- Öffentliche/private Projekteinstellungen

#### Tasks
- Aufgabenverwaltung mit Prioritäten und Status
- Zuweisung an Benutzer
- Fortschrittsverfolgung

#### Documents
- Dokumentenmanagement mit Versionierung
- Verschiedene Dokumententypen (Pläne, Genehmigungen, etc.)
- Tagging und Kategorisierung

#### Milestones
- Meilensteinverwaltung mit kritischen Pfaden
- Terminplanung und -verfolgung

#### Quotes
- Angebotsverwaltung mit KI-Analyse
- Anonyme Angebotsanfragen
- Kontaktfreigabe nach Annahme

#### Messages
- In-App-Kommunikation
- Nachrichtenverlauf und -status

## 🔐 Sicherheit

- **JWT-basierte Authentifizierung**
- **Passwort-Hashing** mit bcrypt
- **CORS-Konfiguration**
- **Input-Validierung** mit Pydantic
- **SQL-Injection-Schutz** durch SQLAlchemy ORM
- **Rate-Limiting** (implementierbar)

## 🧪 Tests

```bash
# Alle Tests ausführen
pytest

# Tests mit Coverage
pytest --cov=app

# Spezifische Tests
pytest tests/test_auth.py
pytest tests/test_projects.py
```

## 📦 Docker-Support

### Docker Compose
```bash
docker-compose up -d
```

### Einzelner Container
```bash
docker build -t buildwise .
docker run -p 8000:8000 buildwise
```

## 🔄 Migrationen

```bash
# Neue Migration erstellen
alembic revision --autogenerate -m "Beschreibung der Änderung"

# Migrationen ausführen
alembic upgrade head

# Migrationen zurücksetzen
alembic downgrade -1
```

## 📊 Monitoring & Logging

- **Request-Timing**: Automatische Messung der Antwortzeiten
- **Exception-Handling**: Globale Fehlerbehandlung
- **Health-Checks**: Endpunkt für Service-Monitoring

## 🚀 Deployment

### Produktionsumgebung
1. **Umgebungsvariablen** für Produktion konfigurieren
2. **CORS-Einstellungen** anpassen
3. **Trusted Hosts** konfigurieren
4. **SSL/TLS** einrichten
5. **Reverse Proxy** (nginx) konfigurieren
6. **Datenbank-Backups** einrichten

### Cloud-Deployment
- **AWS**: ECS/Fargate mit RDS
- **Google Cloud**: Cloud Run mit Cloud SQL
- **Azure**: App Service mit Azure Database

## 🔮 Zukünftige Erweiterungen

- **Elasticsearch** für Volltextsuche
- **Redis** für Caching und Session-Management
- **Celery** für asynchrone Aufgaben
- **Stripe** für Zahlungsabwicklung
- **SendGrid** für E-Mail-Versand
- **AWS S3** für Dokumentenspeicherung
- **WebSocket** für Echtzeit-Kommunikation

## 🤝 Beitragen

1. Fork des Repositories
2. Feature-Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Änderungen committen (`git commit -m 'Add some AmazingFeature'`)
4. Branch pushen (`git push origin feature/AmazingFeature`)
5. Pull Request erstellen

## 📄 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert.

## 📞 Support

Bei Fragen oder Problemen:

- **Issues**: GitHub Issues verwenden
- **Dokumentation**: `/docs` Endpunkt der API
- **E-Mail**: support@buildwise.com

## 🏗 Projektstruktur

```
BuildWise/
├── app/
│   ├── api/                 # API-Router
│   │   ├── auth.py         # Authentifizierung
│   │   ├── users.py        # Benutzerverwaltung
│   │   ├── projects.py     # Projektmanagement
│   │   ├── tasks.py        # Aufgabenverwaltung
│   │   ├── documents.py    # Dokumentenmanagement
│   │   ├── milestones.py   # Meilensteinmanagement
│   │   ├── quotes.py       # Angebotsverwaltung
│   │   └── messages.py     # Nachrichtenverwaltung
│   ├── core/               # Kernfunktionen
│   │   ├── config.py       # Konfiguration
│   │   ├── database.py     # Datenbankverbindung
│   │   └── security.py     # Sicherheitsfunktionen
│   ├── models/             # Datenbankmodelle
│   ├── schemas/            # Pydantic-Schemas
│   ├── services/           # Geschäftslogik
│   └── main.py            # Hauptanwendung
├── migrations/             # Datenbankmigrationen
├── tests/                  # Tests
├── storage/                # Dateispeicherung
├── requirements.txt        # Python-Abhängigkeiten
├── docker-compose.yml      # Docker-Konfiguration
└── README.md              # Diese Datei
```

---

**BuildWise** - Der digitale Assistent für Ihre Immobilienprojekte! 🏠✨
