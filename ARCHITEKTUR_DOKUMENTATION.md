# BuildWise - Architektur-Dokumentation

## Übersicht

BuildWise ist eine Full-Stack-Anwendung mit React/TypeScript Frontend und FastAPI Python Backend. Diese Dokumentation erklärt die detaillierte Kommunikation zwischen Frontend und Backend sowie die Datenströme für den späteren Umbau auf PostgreSQL.

## 1. Technologie-Stack

### Frontend
- **Framework**: React 19.1.0 mit TypeScript
- **Build-Tool**: Vite 7.0.0
- **Styling**: Tailwind CSS 3.3.3
- **HTTP-Client**: Axios 1.10.0
- **Routing**: React Router DOM 7.6.3
- **Charts**: Chart.js 4.5.0, Recharts 2.9.0
- **Icons**: Lucide React 0.525.0

### Backend
- **Framework**: FastAPI (Python)
- **Datenbank**: SQLite (Entwicklung) → PostgreSQL (Produktion)
- **ORM**: SQLAlchemy 2.0+ (Async)
- **Authentifizierung**: JWT (JSON Web Tokens)
- **Validierung**: Pydantic
- **Dokumentation**: Auto-generierte OpenAPI/Swagger Docs

## 2. Netzwerk-Konfiguration

### Frontend (Port 5173)
```typescript
// Frontend/Frontend/src/api/api.ts
export const getApiBaseUrl = () => {
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:8000/api/v1';
  }
  return `http://${hostname}:8000/api/v1`;
};
```

### Backend (Port 8000)
```python
# app/main.py
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 3. Authentifizierung & Sicherheit

### JWT-Token-Flow
```typescript
// Frontend: Token-Management
const api = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Automatischer Token-Header
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token && !config.url?.includes('/auth/login')) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### Backend-Authentifizierung
```python
# app/api/deps.py
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    return user
```

## 4. API-Endpunkte & Datenströme

### 4.1 Authentifizierung (`/api/v1/auth/`)

#### Login-Flow
```typescript
// Frontend: Login-Request
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin@buildwise.de&password=admin123
```

```python
# Backend: Login-Handler
@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Falsche E-Mail oder Passwort")
    
    token = create_access_token({"sub": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "user_type": user.user_type,
            "consents": {...}
        }
    }
```

#### Response-Format
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "admin@buildwise.de",
    "first_name": "Admin",
    "last_name": "User",
    "user_type": "PROFESSIONAL",
    "consents": {
      "data_processing": true,
      "marketing": false,
      "privacy_policy": true,
      "terms": true
    }
  }
}
```

### 4.2 Projekte (`/api/v1/projects/`)

#### Projekte abrufen
```typescript
// Frontend: Projekte laden
export async function getProjects() {
  const res = await api.get('/projects');
  return res.data;
}
```

```python
# Backend: Projekte-Endpunkt
@router.get("/", response_model=List[ProjectSummary])
async def read_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    projects = await get_projects_for_user(db, current_user.id)
    return projects
```

#### Datenbank-Query
```python
# app/services/project_service.py
async def get_projects_for_user(db: AsyncSession, owner_id: int) -> List[Project]:
    result = await db.execute(
        select(Project).where(Project.owner_id == owner_id)
    )
    return list(result.scalars().all())
```

#### Response-Format
```json
[
  {
    "id": 1,
    "name": "Mein Bauprojekt",
    "description": "Ein Wohnhaus in München",
    "project_type": "NEW_BUILD",
    "status": "PLANNING",
    "progress_percentage": 25.5,
    "budget": 500000,
    "current_costs": 125000,
    "start_date": "2024-01-15",
    "end_date": "2024-12-31",
    "address": "München, Bayern",
    "is_public": true,
    "allow_quotes": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-20T14:45:00Z"
  }
]
```

### 4.3 Milestones (`/api/v1/milestones/`)

#### Milestones für Projekt abrufen
```typescript
// Frontend: Milestones laden
export async function getMilestones(project_id: number) {
  const res = await api.get('/milestones', { params: { project_id } });
  return res.data;
}
```

```python
# Backend: Milestones-Endpunkt
@router.get("/", response_model=List[MilestoneRead])
async def read_milestones(
    project_id: int = Query(..., description="Projekt-ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    milestones = await get_milestones_for_project(db, project_id)
    return milestones
```

### 4.4 Tasks (`/api/v1/tasks/`)

#### Tasks für Projekt abrufen
```typescript
// Frontend: Tasks laden
export async function getTasks(project_id?: number) {
  const params = project_id ? { project_id } : {};
  const res = await api.get('/tasks', { params });
  return res.data;
}
```

### 4.5 Dokumente (`/api/v1/documents/`)

#### Dokumente hochladen
```typescript
// Frontend: Dokument-Upload
export async function uploadDocument(formData: FormData) {
  const res = await api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return res.data;
}
```

```python
# Backend: Dokument-Upload
@router.post("/upload", response_model=DocumentRead)
async def upload_document(
    file: UploadFile = File(...),
    project_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(None),
    document_type: str = Form("other"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    document = await create_document(db, current_user.id, project_id, file, title, description, document_type)
    return document
```

### 4.6 Quotes (`/api/v1/quotes/`)

#### Angebote für Milestone abrufen
```typescript
// Frontend: Quotes laden
export async function getQuotesForMilestone(milestone_id: number) {
  const response = await api.get(`/quotes/milestone/${milestone_id}`);
  return response.data;
}
```

## 5. Datenbank-Schema (SQLite → PostgreSQL)

### 5.1 Aktuelle SQLite-Struktur

```sql
-- Haupttabellen
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    first_name VARCHAR,
    last_name VARCHAR,
    user_type VARCHAR DEFAULT 'PROFESSIONAL',
    status VARCHAR DEFAULT 'ACTIVE',
    data_processing_consent BOOLEAN DEFAULT FALSE,
    marketing_consent BOOLEAN DEFAULT FALSE,
    privacy_policy_accepted BOOLEAN DEFAULT FALSE,
    terms_accepted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    owner_id INTEGER REFERENCES users(id),
    name VARCHAR NOT NULL,
    description TEXT,
    project_type VARCHAR NOT NULL, -- NEW_BUILD, RENOVATION, EXTENSION, REFURBISHMENT
    status VARCHAR NOT NULL, -- PLANNING, PREPARATION, CONSTRUCTION, COMPLETED, CANCELLED
    address VARCHAR,
    property_size REAL,
    construction_area REAL,
    start_date DATE,
    end_date DATE,
    estimated_duration INTEGER,
    budget REAL,
    current_costs REAL DEFAULT 0,
    progress_percentage REAL DEFAULT 0,
    is_public BOOLEAN DEFAULT FALSE,
    allow_quotes BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE milestones (
    id INTEGER PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    title VARCHAR NOT NULL,
    description TEXT,
    status VARCHAR NOT NULL, -- PLANNED, IN_PROGRESS, COMPLETED, CANCELLED
    priority VARCHAR DEFAULT 'MEDIUM', -- LOW, MEDIUM, HIGH, CRITICAL
    planned_date DATE NOT NULL,
    start_date DATE,
    end_date DATE,
    progress_percentage REAL DEFAULT 0,
    budget REAL,
    actual_costs REAL,
    contractor VARCHAR,
    is_critical BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    title VARCHAR NOT NULL,
    description TEXT,
    status VARCHAR NOT NULL, -- TODO, IN_PROGRESS, REVIEW, COMPLETED, CANCELLED
    priority VARCHAR DEFAULT 'MEDIUM', -- LOW, MEDIUM, HIGH, URGENT
    assigned_to INTEGER REFERENCES users(id),
    created_by INTEGER REFERENCES users(id),
    due_date DATE,
    estimated_hours INTEGER,
    actual_hours INTEGER,
    progress_percentage REAL DEFAULT 0,
    is_milestone BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE quotes (
    id INTEGER PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    milestone_id INTEGER REFERENCES milestones(id),
    service_provider_id INTEGER REFERENCES users(id),
    title VARCHAR NOT NULL,
    description TEXT,
    status VARCHAR NOT NULL, -- DRAFT, SUBMITTED, UNDER_REVIEW, ACCEPTED, REJECTED, EXPIRED
    total_amount REAL NOT NULL,
    currency VARCHAR DEFAULT 'EUR',
    valid_until DATE,
    labor_cost REAL,
    material_cost REAL,
    overhead_cost REAL,
    estimated_duration INTEGER,
    start_date DATE,
    completion_date DATE,
    payment_terms VARCHAR,
    warranty_period INTEGER,
    risk_score INTEGER,
    price_deviation REAL,
    ai_recommendation TEXT,
    contact_released BOOLEAN DEFAULT FALSE,
    company_name VARCHAR,
    contact_person VARCHAR,
    phone VARCHAR,
    email VARCHAR,
    website VARCHAR,
    pdf_upload_path VARCHAR,
    additional_documents TEXT,
    rating INTEGER,
    feedback TEXT,
    rejection_reason TEXT,
    submitted_at TIMESTAMP,
    accepted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    uploaded_by INTEGER REFERENCES users(id),
    title VARCHAR NOT NULL,
    description TEXT,
    document_type VARCHAR NOT NULL, -- PLAN, PERMIT, QUOTE, INVOICE, CONTRACT, PHOTO, OTHER
    file_name VARCHAR NOT NULL,
    file_path VARCHAR NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR NOT NULL,
    version INTEGER DEFAULT 1,
    is_latest BOOLEAN DEFAULT TRUE,
    tags VARCHAR,
    category VARCHAR,
    is_public BOOLEAN DEFAULT FALSE,
    is_encrypted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    sender_id INTEGER REFERENCES users(id),
    recipient_id INTEGER REFERENCES users(id),
    content TEXT NOT NULL,
    message_type VARCHAR DEFAULT 'TEXT', -- TEXT, DOCUMENT, SYSTEM, NOTIFICATION
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cost_positions (
    id INTEGER PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    quote_id INTEGER REFERENCES quotes(id),
    milestone_id INTEGER REFERENCES milestones(id),
    title VARCHAR NOT NULL,
    description TEXT,
    amount REAL NOT NULL,
    currency VARCHAR DEFAULT 'EUR',
    category VARCHAR NOT NULL,
    cost_type VARCHAR, -- MATERIAL, LABOR, EQUIPMENT, SERVICES, PERMITS, OTHER
    status VARCHAR DEFAULT 'PLANNED', -- PLANNED, IN_PROGRESS, COMPLETED, CANCELLED
    contractor_name VARCHAR,
    contractor_contact VARCHAR,
    contractor_phone VARCHAR,
    contractor_email VARCHAR,
    contractor_website VARCHAR,
    progress_percentage REAL DEFAULT 0,
    paid_amount REAL DEFAULT 0,
    payment_terms VARCHAR,
    warranty_period INTEGER,
    estimated_duration INTEGER,
    start_date DATE,
    completion_date DATE,
    labor_cost REAL,
    material_cost REAL,
    overhead_cost REAL,
    risk_score INTEGER,
    price_deviation REAL,
    ai_recommendation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR NOT NULL,
    description TEXT,
    resource_type VARCHAR,
    resource_id INTEGER,
    ip_address VARCHAR,
    user_agent VARCHAR,
    risk_level VARCHAR DEFAULT 'LOW',
    processing_purpose VARCHAR,
    legal_basis VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5.2 PostgreSQL-Migration

#### Migration-Skript
```python
# migrations/001_initial_schema.py
"""Initial schema migration for PostgreSQL"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('user_type', sa.Enum('PROFESSIONAL', 'SERVICE_PROVIDER', name='usertype'), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'SUSPENDED', name='userstatus'), nullable=True),
        sa.Column('data_processing_consent', sa.Boolean(), nullable=True),
        sa.Column('marketing_consent', sa.Boolean(), nullable=True),
        sa.Column('privacy_policy_accepted', sa.Boolean(), nullable=True),
        sa.Column('terms_accepted', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('project_type', sa.Enum('NEW_BUILD', 'RENOVATION', 'EXTENSION', 'REFURBISHMENT', name='projecttype'), nullable=False),
        sa.Column('status', sa.Enum('PLANNING', 'PREPARATION', 'CONSTRUCTION', 'COMPLETED', 'CANCELLED', name='projectstatus'), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('property_size', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('construction_area', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('estimated_duration', sa.Integer(), nullable=True),
        sa.Column('budget', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('current_costs', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('progress_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('allow_quotes', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Weitere Tabellen...

def downgrade():
    op.drop_table('projects')
    op.drop_table('users')
    # Weitere Tabellen...
```

#### Datenbank-Konfiguration für PostgreSQL
```python
# app/core/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from .config import get_settings

settings = get_settings()

# PostgreSQL für Produktion
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/buildwise"

# SQLite für Entwicklung
if settings.ENVIRONMENT == "development":
    DATABASE_URL = "sqlite+aiosqlite:///./buildwise.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    # PostgreSQL-spezifische Einstellungen
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """Yield an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

## 6. Error Handling & Logging

### 6.1 Frontend Error Handling
```typescript
// Frontend/Frontend/src/api/api.ts
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`, response.data);
    return response;
  },
  async (error) => {
    console.error('❌ Response Error:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      url: error.config?.url,
      data: error.response?.data,
      message: error.message
    });
    
    // Token-Refresh bei 401 Fehlern
    if (error.response?.status === 401 && !error.config?.url?.includes('/auth/login')) {
      // Token-Refresh-Logik...
    }
    
    return Promise.reject(error);
  }
);
```

### 6.2 Backend Error Handling
```python
# app/main.py
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "traceback": traceback.format_exc() if settings.DEBUG else None
        }
    )
```

## 7. Performance & Optimierung

### 7.1 Frontend-Optimierungen
- **Lazy Loading**: React.lazy() für Code-Splitting
- **Memoization**: React.memo() für teure Komponenten
- **Virtual Scrolling**: Für große Listen
- **Image Optimization**: WebP-Format, Lazy Loading

### 7.2 Backend-Optimierungen
- **Database Indexing**: Für häufige Queries
- **Connection Pooling**: PostgreSQL
- **Caching**: Redis für Session-Daten
- **Async/Await**: Vollständig asynchrone API

### 7.3 Database-Optimierungen (PostgreSQL)
```sql
-- Indizes für häufige Queries
CREATE INDEX idx_projects_owner_id ON projects(owner_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_milestones_project_id ON milestones(project_id);
CREATE INDEX idx_tasks_project_id ON tasks(project_id);
CREATE INDEX idx_quotes_project_id ON quotes(project_id);
CREATE INDEX idx_documents_project_id ON documents(project_id);

-- Composite Indizes
CREATE INDEX idx_projects_owner_status ON projects(owner_id, status);
CREATE INDEX idx_milestones_project_status ON milestones(project_id, status);
```

## 8. Deployment & Hosting

### 8.1 Frontend Deployment
```bash
# Build für Produktion
npm run build

# Nginx-Konfiguration
server {
    listen 80;
    server_name buildwise.com;
    
    location / {
        root /var/www/buildwise/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 8.2 Backend Deployment
```bash
# Gunicorn mit Uvicorn Workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Docker Compose
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/buildwise
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=buildwise
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 9. Monitoring & Logging

### 9.1 Application Monitoring
```python
# app/core/monitoring.py
import logging
from fastapi import Request
import time

logger = logging.getLogger(__name__)

async def log_request(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s"
    )
    
    return response
```

### 9.2 Database Monitoring
```sql
-- PostgreSQL Performance-Queries
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = 'public';

-- Slow Query Log
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

## 10. Sicherheit

### 10.1 CORS-Konfiguration
```python
# Produktions-CORS
allowed_origins = [
    "https://buildwise.com",
    "https://www.buildwise.com",
    "https://app.buildwise.com"
]
```

### 10.2 Rate Limiting
```python
# app/core/rate_limiter.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    # Login-Logik
```

### 10.3 Input Validation
```python
# Pydantic-Schemas für Validierung
from pydantic import BaseModel, EmailStr, validator

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Passwort muss mindestens 8 Zeichen lang sein')
        return v
```

Diese Dokumentation bietet eine vollständige Übersicht der BuildWise-Architektur und dient als Grundlage für den späteren Umbau auf PostgreSQL und das Produktions-Deployment. 