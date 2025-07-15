# Gewerk-Erstellung: Frontend-Backend Datenfluss

## Übersicht des Gewerk-Erstellungsprozesses

```mermaid
graph TB
    subgraph "Frontend (React)"
        User[Benutzer]
        TradeForm[Gewerk-Formular]
        QuoteService[Quote Service]
        APIClient[Axios Client]
        AuthContext[Auth Context]
    end

    subgraph "Backend (FastAPI)"
        QuoteAPI[Quote API Endpoint]
        Validation[Pydantic Validation]
        QuoteService[Quote Service Layer]
        DatabaseService[Database Service]
    end

    subgraph "Datenbank"
        SQLite[SQLite Database]
        ProjectsTable[projects Table]
        QuotesTable[quotes Table]
        UsersTable[users Table]
    end

    User --> TradeForm
    TradeForm --> QuoteService
    QuoteService --> APIClient
    APIClient --> QuoteAPI
    QuoteAPI --> Validation
    Validation --> QuoteService
    QuoteService --> DatabaseService
    DatabaseService --> SQLite

    AuthContext --> APIClient
```

## Detaillierter Sequenzablauf

```mermaid
sequenceDiagram
    participant U as Benutzer
    participant F as Frontend (Quotes.tsx)
    participant QS as QuoteService
    participant AC as Axios Client
    participant B as Backend (Quote API)
    participant V as Validation
    participant QSrv as Quote Service Layer
    participant DB as SQLite Database
    participant Auth as Auth Context

    Note over U,Auth: 1. Benutzer öffnet Gewerk-Formular
    U->>F: Klickt "Gewerk erstellen"
    F->>F: Öffnet Modal mit Formular
    F->>Auth: Prüft Benutzer-Authentifizierung
    Auth-->>F: Token verfügbar

    Note over U,Auth: 2. Benutzer füllt Formular aus
    U->>F: Füllt Gewerk-Daten aus:
    Note over F: - Titel: "Elektroinstallation"
    Note over F: - Beschreibung: "Komplette Elektroinstallation"
    Note over F: - Budget: 15000 €
    Note over F: - Kategorie: "Elektro"
    Note over F: - Priorität: "Hoch"
    Note over F: - Geplantes Datum: 2024-03-15
    Note over F: - Projekt: Projekt ID 4

    Note over U,Auth: 3. Frontend bereitet Daten vor
    F->>F: Validiert Formular-Daten
    F->>F: Erstellt JSON-Objekt:
    Note over F: {
    Note over F:   "title": "Elektroinstallation",
    Note over F:   "description": "Komplette Elektroinstallation",
    Note over F:   "project_id": 4,
    Note over F:   "status": "planned",
    Note over F:   "priority": "high",
    Note over F:   "category": "Elektro",
    Note over F:   "budget": 15000,
    Note over F:   "planned_date": "2024-03-15",
    Note over F:   "is_critical": true,
    Note over F:   "notify_on_completion": true
    Note over F: }

    Note over U,Auth: 4. API-Service wird aufgerufen
    F->>QS: createTrade(tradeData)
    QS->>AC: POST /api/v1/quotes/ (mit Token)
    AC->>AC: Fügt Authorization Header hinzu
    Note over AC: Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

    Note over U,Auth: 5. Backend empfängt Request
    AC->>B: HTTP POST Request
    Note over B: Endpoint: /api/v1/quotes/
    Note over B: Headers: Content-Type: application/json
    Note over B: Body: JSON-Daten des Gewerks

    Note over U,Auth: 6. Backend-Validierung
    B->>V: Validiert eingehende Daten
    V->>V: Prüft Pydantic Schema:
    Note over V: - title: required, string
    Note over V: - description: optional, string
    Note over V: - project_id: required, integer
    Note over V: - status: enum (planned, in_progress, completed)
    Note over V: - priority: enum (low, medium, high, critical)
    Note over V: - budget: optional, decimal
    Note over V: - planned_date: required, date

    Note over U,Auth: 7. Service Layer Verarbeitung
    V-->>B: Validierung erfolgreich
    B->>QSrv: create_quote(trade_data)
    QSrv->>QSrv: Erstellt Quote-Objekt
    QSrv->>QSrv: Setzt Standard-Werte:
    Note over QSrv: - status: "planned"
    Note over QSrv: - progress_percentage: 0
    Note over QSrv: - created_at: datetime.now()
    Note over QSrv: - updated_at: datetime.now()

    Note over U,Auth: 8. Datenbank-Operation
    QSrv->>DB: INSERT INTO quotes
    Note over DB: SQL Query:
    Note over DB: INSERT INTO quotes (
    Note over DB:   title, description, project_id, status,
    Note over DB:   priority, category, budget, planned_date,
    Note over DB:   is_critical, notify_on_completion,
    Note over DB:   created_at, updated_at
    Note over DB: ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

    Note over U,Auth: 9. Datenbank-Response
    DB-->>QSrv: Neue Quote-ID: 123
    QSrv->>QSrv: Lädt vollständige Quote-Daten
    QSrv->>DB: SELECT * FROM quotes WHERE id = 123
    DB-->>QSrv: Vollständige Quote-Daten

    Note over U,Auth: 10. Backend-Response
    QSrv-->>B: Quote-Objekt mit ID
    B->>B: Erstellt JSON-Response
    Note over B: {
    Note over B:   "id": 123,
    Note over B:   "title": "Elektroinstallation",
    Note over B:   "description": "Komplette Elektroinstallation",
    Note over B:   "project_id": 4,
    Note over B:   "status": "planned",
    Note over B:   "priority": "high",
    Note over B:   "category": "Elektro",
    Note over B:   "budget": 15000.00,
    Note over B:   "planned_date": "2024-03-15",
    Note over B:   "is_critical": true,
    Note over B:   "notify_on_completion": true,
    Note over B:   "progress_percentage": 0,
    Note over B:   "created_at": "2024-01-15T10:30:00",
    Note over B:   "updated_at": "2024-01-15T10:30:00"
    Note over B: }

    Note over U,Auth: 11. Frontend empfängt Response
    B-->>AC: HTTP 201 Created + JSON
    AC-->>QS: Response-Daten
    QS-->>F: Quote-Objekt

    Note over U,Auth: 12. Frontend-Update
    F->>F: Fügt neues Gewerk zur Liste hinzu
    F->>F: Schließt Modal
    F->>F: Zeigt Erfolgsmeldung
    F-->>U: "Gewerk erfolgreich erstellt!"
```

## Frontend Code-Ablauf (Quotes.tsx)

```mermaid
graph TD
    subgraph "Frontend Code Flow"
        A[handleCreateTrade] --> B[Validiere Formular-Daten]
        B --> C{Validierung OK?}
        C -->|Nein| D[Zeige Fehlermeldung]
        C -->|Ja| E[Erstelle tradeData Objekt]
        E --> F[QuoteService.createQuote]
        F --> G[Axios POST Request]
        G --> H{Request erfolgreich?}
        H -->|Nein| I[Zeige Error Toast]
        H -->|Ja| J[Update UI State]
        J --> K[Schließe Modal]
        K --> L[Zeige Success Toast]
        L --> M[Lade Gewerke neu]
    end

    subgraph "Formular-Validierung"
        N[Prüfe Titel] --> O[Prüfe Projekt-ID]
        O --> P[Prüfe Datum]
        P --> Q[Prüfe Budget]
        Q --> R[Prüfe Kategorie]
    end

    subgraph "Error Handling"
        S[Network Error] --> T[Zeige "Verbindungsfehler"]
        U[Validation Error] --> V[Zeige spezifische Fehler]
        W[Server Error] --> X[Zeige "Server-Fehler"]
    end
```

## Backend Code-Ablauf (Quote API)

```mermaid
graph TD
    subgraph "Backend API Flow"
        A1[POST /quotes/] --> B1[Pydantic Validation]
        B1 --> C1{Validation OK?}
        C1 -->|Nein| D1[422 Validation Error]
        C1 -->|Ja| E1[Quote Service Layer]
        E1 --> F1[Database Operation]
        F1 --> G1{DB Operation OK?}
        G1 -->|Nein| H1[500 Database Error]
        G1 -->|Ja| I1[Return Quote Object]
    end

    subgraph "Database Operations"
        J1[INSERT INTO quotes] --> K1[Get New ID]
        K1 --> L1[SELECT * FROM quotes WHERE id = ?]
        L1 --> M1[Return Full Quote Data]
    end

    subgraph "Validation Rules"
        N1[title: required, max 255 chars]
        O1[project_id: required, exists in projects]
        P1[status: enum values only]
        Q1[priority: enum values only]
        R1[budget: optional, positive number]
        S1[planned_date: required, valid date]
    end
```

## Datenstrukturen

```mermaid
graph LR
    subgraph "Frontend Trade Data"
        FT[Trade Form Data]
        FT --> FT1[title: string]
        FT --> FT2[description: string]
        FT --> FT3[project_id: number]
        FT --> FT4[status: string]
        FT --> FT5[priority: string]
        FT --> FT6[category: string]
        FT --> FT7[budget: number]
        FT --> FT8[planned_date: string]
        FT --> FT9[is_critical: boolean]
        FT --> FT10[notify_on_completion: boolean]
    end

    subgraph "Backend Quote Model"
        BQ[Quote Database Model]
        BQ --> BQ1[id: integer PK]
        BQ --> BQ2[title: string]
        BQ --> BQ3[description: text]
        BQ --> BQ4[project_id: integer FK]
        BQ --> BQ5[status: enum]
        BQ --> BQ6[priority: enum]
        BQ --> BQ7[category: string]
        BQ --> BQ8[budget: decimal]
        BQ --> BQ9[planned_date: date]
        BQ --> BQ10[is_critical: boolean]
        BQ --> BQ11[notify_on_completion: boolean]
        BQ --> BQ12[progress_percentage: integer]
        BQ --> BQ13[created_at: datetime]
        BQ --> BQ14[updated_at: datetime]
    end

    subgraph "API Response"
        AR[API Response JSON]
        AR --> AR1[HTTP 201 Created]
        AR --> AR2[Location Header]
        AR --> AR3[Quote Object]
        AR --> AR4[Success Message]
    end
```

## Error Handling Szenarien

```mermaid
sequenceDiagram
    participant U as Benutzer
    participant F as Frontend
    participant B as Backend
    participant DB as Database

    Note over U,DB: Szenario 1: Validierungsfehler
    U->>F: Leeres Titel-Feld
    F->>B: POST /quotes/ (ohne title)
    B->>B: Pydantic Validation
    B-->>F: 422 Validation Error
    F-->>U: "Titel ist erforderlich"

    Note over U,DB: Szenario 2: Datenbankfehler
    U->>F: Gültige Daten
    F->>B: POST /quotes/
    B->>DB: INSERT (DB offline)
    DB-->>B: Connection Error
    B-->>F: 500 Internal Server Error
    F-->>U: "Datenbankfehler - versuchen Sie es später"

    Note over U,DB: Szenario 3: Token abgelaufen
    U->>F: Gewerk erstellen
    F->>B: POST /quotes/ (ungültiger Token)
    B-->>F: 401 Unauthorized
    F->>F: Token-Refresh versuchen
    F->>B: POST /auth/refresh
    B-->>F: Neuer Token
    F->>B: Wiederhole ursprünglichen Request
    B-->>F: 201 Created
    F-->>U: Gewerk erstellt
```

## Datenbank-Schema für Quotes

```mermaid
erDiagram
    quotes {
        int id PK
        string title
        text description
        string status
        string priority
        string category
        decimal budget
        date planned_date
        date start_date
        date end_date
        boolean is_critical
        boolean notify_on_completion
        int progress_percentage
        int project_id FK
        int service_provider_id FK
        datetime created_at
        datetime updated_at
    }

    projects {
        int id PK
        string name
        string description
        int user_id FK
    }

    users {
        int id PK
        string email
        string first_name
        string last_name
    }

    quotes ||--o{ projects : "belongs_to"
    quotes ||--o{ users : "service_provider"
    projects ||--o{ users : "owned_by"
```

## Zusammenfassung des Datenflusses

### **1. Frontend-Initiation**
- Benutzer klickt "Gewerk erstellen"
- Modal-Formular öffnet sich
- AuthContext prüft Benutzer-Token

### **2. Daten-Validierung**
- Frontend validiert Formular-Daten
- Erstellt strukturiertes JSON-Objekt
- Bereitet API-Request vor

### **3. API-Kommunikation**
- Axios sendet POST-Request mit Token
- Backend empfängt und validiert Daten
- Pydantic-Schema prüft Datentypen

### **4. Datenbank-Operation**
- Service Layer erstellt Quote-Objekt
- SQLAlchemy führt INSERT aus
- Neue Quote-ID wird generiert

### **5. Response-Handling**
- Backend sendet 201 Created + JSON
- Frontend aktualisiert UI-State
- Erfolgsmeldung wird angezeigt

### **6. Error-Handling**
- Validierungsfehler: 422 + spezifische Meldungen
- Datenbankfehler: 500 + generische Meldung
- Token-Fehler: 401 + automatischer Refresh

Dieser Datenfluss zeigt die vollständige Integration zwischen Frontend und Backend beim Erstellen eines Gewerks in BuildWise. 