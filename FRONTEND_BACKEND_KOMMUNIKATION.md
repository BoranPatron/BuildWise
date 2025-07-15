# Frontend-Backend Kommunikation in BuildWise

## Übersicht der Architektur

```mermaid
graph TB
    %% Frontend-Komponenten
    subgraph "Frontend (React + TypeScript)"
        UI[React UI Components]
        AuthCtx[AuthContext]
        APIClient[Axios API Client]
        Services[API Services]
        Router[React Router]
    end

    %% Backend-Komponenten
    subgraph "Backend (FastAPI + Python)"
        FastAPI[FastAPI Server]
        AuthAPI[Auth API]
        ProjectAPI[Project API]
        TaskAPI[Task API]
        DocumentAPI[Document API]
        QuoteAPI[Quote API]
        MessageAPI[Message API]
        MilestoneAPI[Milestone API]
        CostPositionAPI[Cost Position API]
        BuildWiseFeeAPI[BuildWise Fee API]
    end

    %% Datenbank
    subgraph "Datenbank"
        SQLite[SQLite Database]
        Migrations[Alembic Migrations]
    end

    %% Externe Services
    subgraph "Externe Services"
        JWT[JWT Token Service]
        FileStorage[File Storage]
        EmailService[Email Service]
    end

    %% Netzwerk-Konfiguration
    subgraph "Netzwerk"
        CORS[CORS Middleware]
        Proxy[Reverse Proxy]
    end

    %% Frontend zu Backend Verbindungen
    UI --> AuthCtx
    AuthCtx --> APIClient
    APIClient --> Services
    Services --> FastAPI

    %% Backend API Routen
    FastAPI --> AuthAPI
    FastAPI --> ProjectAPI
    FastAPI --> TaskAPI
    FastAPI --> DocumentAPI
    FastAPI --> QuoteAPI
    FastAPI --> MessageAPI
    FastAPI --> MilestoneAPI
    FastAPI --> CostPositionAPI
    FastAPI --> BuildWiseFeeAPI

    %% Backend zu Datenbank
    AuthAPI --> SQLite
    ProjectAPI --> SQLite
    TaskAPI --> SQLite
    DocumentAPI --> SQLite
    QuoteAPI --> SQLite
    MessageAPI --> SQLite
    MilestoneAPI --> SQLite
    CostPositionAPI --> SQLite
    BuildWiseFeeAPI --> SQLite

    %% Middleware und Services
    FastAPI --> CORS
    FastAPI --> JWT
    DocumentAPI --> FileStorage
    AuthAPI --> EmailService

    %% Datenbank-Migration
    SQLite --> Migrations

    %% Styling
    classDef frontend fill:#e1f5fe
    classDef backend fill:#f3e5f5
    classDef database fill:#e8f5e8
    classDef external fill:#fff3e0

    class UI,AuthCtx,APIClient,Services,Router frontend
    class FastAPI,AuthAPI,ProjectAPI,TaskAPI,DocumentAPI,QuoteAPI,MessageAPI,MilestoneAPI,CostPositionAPI,BuildWiseFeeAPI backend
    class SQLite,Migrations database
    class JWT,FileStorage,EmailService,CORS,Proxy external
```

## Detaillierter Authentifizierungs-Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant DB as Database
    participant JWT as JWT Service

    Note over U,DB: Login-Prozess
    U->>F: Login mit Email/Password
    F->>B: POST /api/v1/auth/login
    B->>DB: Prüfe Benutzer-Credentials
    DB-->>B: Benutzer-Daten
    B->>JWT: Erstelle Access Token
    JWT-->>B: JWT Token
    B-->>F: Token + User Data
    F->>F: Speichere Token in localStorage
    F-->>U: Weiterleitung zum Dashboard

    Note over U,DB: API-Requests mit Token
    U->>F: Navigiere zu geschützter Seite
    F->>B: GET /api/v1/projects (mit Bearer Token)
    B->>JWT: Validiere Token
    JWT-->>B: Token gültig
    B->>DB: Hole Projekte für User
    DB-->>B: Projekt-Daten
    B-->>F: JSON Response
    F-->>U: Zeige Projekte an

    Note over U,DB: Token-Refresh
    F->>B: API Request (Token abgelaufen)
    B-->>F: 401 Unauthorized
    F->>B: POST /api/v1/auth/refresh
    B->>JWT: Erstelle neuen Token
    JWT-->>B: Neuer Token
    B-->>F: Neuer Token
    F->>F: Update localStorage
    F->>B: Wiederhole ursprünglichen Request
    B-->>F: Erfolgreiche Response
```

## API-Endpunkt Kommunikation

```mermaid
graph LR
    subgraph "Frontend API Services"
        ProjectService[Project Service]
        TaskService[Task Service]
        DocumentService[Document Service]
        QuoteService[Quote Service]
        MessageService[Message Service]
        MilestoneService[Milestone Service]
        CostPositionService[Cost Position Service]
        BuildWiseFeeService[BuildWise Fee Service]
        UserService[User Service]
    end

    subgraph "Backend API Endpoints"
        ProjectsAPI[/api/v1/projects/]
        TasksAPI[/api/v1/tasks/]
        DocumentsAPI[/api/v1/documents/]
        QuotesAPI[/api/v1/quotes/]
        MessagesAPI[/api/v1/messages/]
        MilestonesAPI[/api/v1/milestones/]
        CostPositionsAPI[/api/v1/cost-positions/]
        BuildWiseFeesAPI[/api/v1/buildwise-fees/]
        UsersAPI[/api/v1/users/]
    end

    subgraph "HTTP Methods"
        GET[GET]
        POST[POST]
        PUT[PUT]
        DELETE[DELETE]
        PATCH[PATCH]
    end

    ProjectService --> GET
    ProjectService --> POST
    ProjectService --> PUT
    ProjectService --> DELETE
    GET --> ProjectsAPI
    POST --> ProjectsAPI
    PUT --> ProjectsAPI
    DELETE --> ProjectsAPI

    TaskService --> GET
    TaskService --> POST
    TaskService --> PUT
    TaskService --> DELETE
    GET --> TasksAPI
    POST --> TasksAPI
    PUT --> TasksAPI
    DELETE --> TasksAPI

    DocumentService --> GET
    DocumentService --> POST
    DocumentService --> PUT
    DocumentService --> DELETE
    GET --> DocumentsAPI
    POST --> DocumentsAPI
    PUT --> DocumentsAPI
    DELETE --> DocumentsAPI

    QuoteService --> GET
    QuoteService --> POST
    QuoteService --> PUT
    QuoteService --> DELETE
    GET --> QuotesAPI
    POST --> QuotesAPI
    PUT --> QuotesAPI
    DELETE --> QuotesAPI

    MessageService --> GET
    MessageService --> POST
    MessageService --> PUT
    MessageService --> DELETE
    GET --> MessagesAPI
    POST --> MessagesAPI
    PUT --> MessagesAPI
    DELETE --> MessagesAPI

    MilestoneService --> GET
    MilestoneService --> POST
    MilestoneService --> PUT
    MilestoneService --> DELETE
    GET --> MilestonesAPI
    POST --> MilestonesAPI
    PUT --> MilestonesAPI
    DELETE --> MilestonesAPI

    CostPositionService --> GET
    CostPositionService --> POST
    CostPositionService --> PUT
    CostPositionService --> DELETE
    GET --> CostPositionsAPI
    POST --> CostPositionsAPI
    PUT --> CostPositionsAPI
    DELETE --> CostPositionsAPI

    BuildWiseFeeService --> GET
    BuildWiseFeeService --> POST
    BuildWiseFeeService --> PUT
    BuildWiseFeeService --> DELETE
    GET --> BuildWiseFeesAPI
    POST --> BuildWiseFeesAPI
    PUT --> BuildWiseFeesAPI
    DELETE --> BuildWiseFeesAPI

    UserService --> GET
    UserService --> POST
    UserService --> PUT
    UserService --> DELETE
    GET --> UsersAPI
    POST --> UsersAPI
    PUT --> UsersAPI
    DELETE --> UsersAPI
```

## Datenfluss bei CRUD-Operationen

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant DB as Database
    participant FS as File Storage

    Note over U,FS: CREATE Operation (z.B. neues Projekt)
    U->>F: Fülle Formular aus
    F->>B: POST /api/v1/projects/ (JSON Data)
    B->>B: Validiere Daten
    B->>DB: INSERT INTO projects
    DB-->>B: Neue Projekt-ID
    B-->>F: 201 Created + Projekt-Daten
    F-->>U: Zeige Erfolgsmeldung

    Note over U,FS: READ Operation (z.B. Projekte laden)
    U->>F: Öffne Dashboard
    F->>B: GET /api/v1/projects/ (mit Token)
    B->>DB: SELECT * FROM projects WHERE user_id = ?
    DB-->>B: Projekt-Liste
    B-->>F: 200 OK + JSON Array
    F-->>U: Rendere Projekt-Karten

    Note over U,FS: UPDATE Operation (z.B. Projekt bearbeiten)
    U->>F: Klicke Bearbeiten
    F->>B: PUT /api/v1/projects/{id} (JSON Data)
    B->>DB: UPDATE projects SET ... WHERE id = ?
    DB-->>B: Update erfolgreich
    B-->>F: 200 OK + aktualisierte Daten
    F-->>U: Zeige aktualisierte Ansicht

    Note over U,FS: DELETE Operation (z.B. Projekt löschen)
    U->>F: Klicke Löschen
    F->>B: DELETE /api/v1/projects/{id}
    B->>DB: DELETE FROM projects WHERE id = ?
    DB-->>B: Delete erfolgreich
    B-->>F: 204 No Content
    F-->>U: Entferne aus UI

    Note over U,FS: File Upload (z.B. Dokument)
    U->>F: Wähle Datei aus
    F->>B: POST /api/v1/documents/upload (FormData)
    B->>FS: Speichere Datei
    FS-->>B: Datei-Pfad
    B->>DB: INSERT INTO documents
    DB-->>B: Dokument-ID
    B-->>F: 201 Created + Dokument-Daten
    F-->>U: Zeige Upload-Erfolg
```

## Error Handling und Status Codes

```mermaid
graph TD
    subgraph "Frontend Error Handling"
        AxiosInterceptor[Axios Response Interceptor]
        ErrorBoundary[React Error Boundary]
        ToastNotifications[Toast Notifications]
        RetryLogic[Retry Logic]
    end

    subgraph "Backend Error Responses"
        ValidationError[422 Validation Error]
        UnauthorizedError[401 Unauthorized]
        ForbiddenError[403 Forbidden]
        NotFoundError[404 Not Found]
        ServerError[500 Server Error]
        DatabaseError[Database Connection Error]
    end

    subgraph "HTTP Status Codes"
        Success200[200 OK]
        Created201[201 Created]
        NoContent204[204 No Content]
        BadRequest400[400 Bad Request]
        Unauthorized401[401 Unauthorized]
        Forbidden403[403 Forbidden]
        NotFound404[404 Not Found]
        Conflict409[409 Conflict]
        Unprocessable422[422 Unprocessable Entity]
        ServerError500[500 Internal Server Error]
    end

    AxiosInterceptor --> ValidationError
    AxiosInterceptor --> UnauthorizedError
    AxiosInterceptor --> ForbiddenError
    AxiosInterceptor --> NotFoundError
    AxiosInterceptor --> ServerError
    AxiosInterceptor --> DatabaseError

    ValidationError --> Unprocessable422
    UnauthorizedError --> Unauthorized401
    ForbiddenError --> Forbidden403
    NotFoundError --> NotFound404
    ServerError --> ServerError500
    DatabaseError --> ServerError500

    ErrorBoundary --> ToastNotifications
    AxiosInterceptor --> RetryLogic
    RetryLogic --> AxiosInterceptor
```

## CORS und Sicherheits-Konfiguration

```mermaid
graph LR
    subgraph "Frontend (Port 5173)"
        ReactApp[React App]
        ViteDevServer[Vite Dev Server]
    end

    subgraph "Backend (Port 8000)"
        FastAPIServer[FastAPI Server]
        CORSMiddleware[CORS Middleware]
        SecurityHeaders[Security Headers]
    end

    subgraph "CORS-Konfiguration"
        AllowedOrigins[Allowed Origins]
        AllowedMethods[Allowed Methods]
        AllowedHeaders[Allowed Headers]
        AllowCredentials[Allow Credentials]
    end

    subgraph "Sicherheits-Headers"
        ContentSecurityPolicy[Content-Security-Policy]
        XFrameOptions[X-Frame-Options]
        XContentTypeOptions[X-Content-Type-Options]
        StrictTransportSecurity[HSTS]
    end

    ReactApp --> ViteDevServer
    ViteDevServer --> FastAPIServer
    FastAPIServer --> CORSMiddleware
    CORSMiddleware --> AllowedOrigins
    CORSMiddleware --> AllowedMethods
    CORSMiddleware --> AllowedHeaders
    CORSMiddleware --> AllowCredentials

    FastAPIServer --> SecurityHeaders
    SecurityHeaders --> ContentSecurityPolicy
    SecurityHeaders --> XFrameOptions
    SecurityHeaders --> XContentTypeOptions
    SecurityHeaders --> StrictTransportSecurity

    AllowedOrigins --> |localhost:5173| ReactApp
    AllowedOrigins --> |127.0.0.1:5173| ReactApp
    AllowedMethods --> |GET, POST, PUT, DELETE| ReactApp
    AllowedHeaders --> |Content-Type, Authorization| ReactApp
```

## Datenbank-Schema und Beziehungen

```mermaid
erDiagram
    users {
        int id PK
        string email
        string password_hash
        string first_name
        string last_name
        string user_type
        string status
        datetime created_at
        datetime updated_at
    }

    projects {
        int id PK
        string name
        string description
        string project_type
        string status
        decimal budget
        string address
        datetime start_date
        datetime end_date
        int user_id FK
        datetime created_at
        datetime updated_at
    }

    tasks {
        int id PK
        string title
        string description
        string status
        string priority
        int progress_percentage
        datetime due_date
        int project_id FK
        int assigned_to FK
        int created_by FK
        datetime created_at
        datetime updated_at
    }

    documents {
        int id PK
        string title
        string description
        string document_type
        string file_name
        string file_path
        int file_size
        string mime_type
        int project_id FK
        int uploaded_by FK
        datetime created_at
        datetime updated_at
    }

    quotes {
        int id PK
        string title
        string description
        string status
        decimal total_amount
        string currency
        datetime valid_until
        int project_id FK
        int service_provider_id FK
        datetime created_at
        datetime updated_at
    }

    messages {
        int id PK
        string content
        string message_type
        boolean is_read
        int sender_id FK
        int recipient_id FK
        int project_id FK
        datetime created_at
        datetime updated_at
    }

    milestones {
        int id PK
        string title
        string description
        string status
        string priority
        datetime planned_date
        datetime actual_date
        int project_id FK
        datetime created_at
        datetime updated_at
    }

    cost_positions {
        int id PK
        string title
        string description
        decimal amount
        string currency
        string category
        string status
        int project_id FK
        int quote_id FK
        datetime created_at
        datetime updated_at
    }

    buildwise_fees {
        int id PK
        int user_id FK
        int project_id FK
        int fee_month
        int fee_year
        decimal total_amount
        decimal fee_percentage
        string status
        datetime created_at
        datetime updated_at
    }

    users ||--o{ projects : "owns"
    users ||--o{ tasks : "assigned_to"
    users ||--o{ tasks : "created_by"
    users ||--o{ documents : "uploaded_by"
    users ||--o{ quotes : "service_provider"
    users ||--o{ messages : "sender"
    users ||--o{ messages : "recipient"
    users ||--o{ buildwise_fees : "pays"

    projects ||--o{ tasks : "contains"
    projects ||--o{ documents : "has"
    projects ||--o{ quotes : "receives"
    projects ||--o{ messages : "contains"
    projects ||--o{ milestones : "has"
    projects ||--o{ cost_positions : "has"
    projects ||--o{ buildwise_fees : "generates"

    quotes ||--o{ cost_positions : "creates"
```

## Real-time Kommunikation (WebSocket)

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant WS as WebSocket
    participant B as Backend
    participant DB as Database

    Note over U,DB: WebSocket-Verbindung aufbauen
    U->>F: Öffne Anwendung
    F->>WS: WebSocket.connect()
    WS->>B: Upgrade HTTP zu WebSocket
    B->>B: Authentifiziere WebSocket-Verbindung
    B-->>WS: Verbindung bestätigt
    WS-->>F: WebSocket geöffnet
    F-->>U: Verbindung hergestellt

    Note over U,DB: Real-time Updates
    U->>F: Erstelle neue Nachricht
    F->>B: POST /api/v1/messages/
    B->>DB: Speichere Nachricht
    DB-->>B: Nachricht-ID
    B->>WS: Broadcast Nachricht an alle Clients
    WS-->>F: Neue Nachricht empfangen
    F-->>U: Zeige Nachricht in Echtzeit

    Note over U,DB: Status-Updates
    U->>F: Ändere Task-Status
    F->>B: PUT /api/v1/tasks/{id}
    B->>DB: Update Task-Status
    DB-->>B: Update erfolgreich
    B->>WS: Broadcast Status-Update
    WS-->>F: Status-Update empfangen
    F-->>U: Aktualisiere UI

    Note over U,DB: Benachrichtigungen
    B->>DB: Neue Aktivität erkannt
    DB-->>B: Aktivitäts-Daten
    B->>WS: Sende Benachrichtigung
    WS-->>F: Benachrichtigung empfangen
    F-->>U: Zeige Toast-Notification
```

## Deployment und Produktions-Architektur

```mermaid
graph TB
    subgraph "Client"
        Browser[Web Browser]
    end

    subgraph "CDN/Proxy"
        Nginx[Nginx Reverse Proxy]
        SSL[SSL/TLS Termination]
    end

    subgraph "Frontend (Produktion)"
        ReactBuild[React Build]
        StaticFiles[Static Files]
    end

    subgraph "Backend (Produktion)"
        Gunicorn[Gunicorn WSGI Server]
        FastAPIApp[FastAPI Application]
        Workers[Multiple Workers]
    end

    subgraph "Datenbank (Produktion)"
        PostgreSQL[PostgreSQL Database]
        ConnectionPool[Connection Pool]
    end

    subgraph "File Storage"
        S3Compatible[S3-Compatible Storage]
        CDN[CDN for Assets]
    end

    subgraph "Monitoring"
        Prometheus[Prometheus Metrics]
        Grafana[Grafana Dashboards]
        Logs[Centralized Logging]
    end

    Browser --> Nginx
    Nginx --> SSL
    SSL --> ReactBuild
    SSL --> Gunicorn

    ReactBuild --> StaticFiles
    Gunicorn --> FastAPIApp
    FastAPIApp --> Workers

    Workers --> PostgreSQL
    PostgreSQL --> ConnectionPool

    FastAPIApp --> S3Compatible
    S3Compatible --> CDN

    Gunicorn --> Prometheus
    FastAPIApp --> Logs
    Prometheus --> Grafana
```

## Migration von SQLite zu PostgreSQL

```mermaid
graph LR
    subgraph "Entwicklung (SQLite)"
        SQLiteDev[SQLite Database]
        AlembicDev[Alembic Migrations]
        FastAPIDev[FastAPI Dev Server]
    end

    subgraph "Migration Process"
        SchemaMigration[Schema Migration]
        DataMigration[Data Migration]
        EnumMigration[Enum Value Migration]
        IndexMigration[Index Migration]
    end

    subgraph "Produktion (PostgreSQL)"
        PostgreSQLProd[PostgreSQL Database]
        AlembicProd[Alembic Migrations]
        FastAPIProd[FastAPI Production]
    end

    subgraph "Konfiguration"
        DevConfig[Development Config]
        ProdConfig[Production Config]
        EnvVars[Environment Variables]
    end

    SQLiteDev --> SchemaMigration
    SchemaMigration --> DataMigration
    DataMigration --> EnumMigration
    EnumMigration --> IndexMigration
    IndexMigration --> PostgreSQLProd

    AlembicDev --> SchemaMigration
    AlembicProd --> PostgreSQLProd

    FastAPIDev --> DevConfig
    FastAPIProd --> ProdConfig
    DevConfig --> EnvVars
    ProdConfig --> EnvVars

    DevConfig --> SQLiteDev
    ProdConfig --> PostgreSQLProd
```

## Zusammenfassung der Kommunikations-Patterns

### 1. **RESTful API-Kommunikation**
- Frontend sendet HTTP-Requests an Backend
- Backend verarbeitet Requests und sendet JSON-Responses
- Standardisierte HTTP-Status-Codes für Fehlerbehandlung

### 2. **Authentifizierung & Autorisierung**
- JWT-Token-basierte Authentifizierung
- Automatische Token-Erneuerung im Frontend
- Rollenbasierte Zugriffskontrolle im Backend

### 3. **Real-time Updates**
- WebSocket-Verbindung für Echtzeit-Updates
- Broadcast von Änderungen an alle verbundenen Clients
- Fallback auf Polling bei WebSocket-Ausfall

### 4. **Error Handling**
- Zentrale Fehlerbehandlung im Frontend
- Strukturierte Error-Responses vom Backend
- Benutzerfreundliche Fehlermeldungen

### 5. **Datei-Upload**
- Multipart-Form-Data für Datei-Uploads
- Backend-Validierung von Dateitypen und -größen
- Sichere Dateispeicherung mit eindeutigen Namen

### 6. **CORS & Sicherheit**
- Konfigurierte CORS-Policies für Cross-Origin-Requests
- Security-Headers für XSS-Schutz
- HTTPS in Produktion

### 7. **Datenbank-Integration**
- SQLAlchemy ORM für Datenbankoperationen
- Alembic für Schema-Migrationen
- Connection-Pooling für Performance

Diese Architektur ermöglicht eine skalierbare, sichere und wartbare Kommunikation zwischen Frontend und Backend in BuildWise. 