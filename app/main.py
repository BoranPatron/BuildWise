import os
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
from fastapi.responses import JSONResponse

# Render.com-spezifische Konfiguration
def get_port():
    """Hole Port von Render.com oder verwende Standard"""
    return int(os.environ.get("PORT", 8000))

def get_host():
    """Hole Host von Render.com oder verwende Standard"""
    return os.environ.get("HOST", "0.0.0.0")

# Lebenszyklus-Manager für die Anwendung
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starte BuildWise Backend...")
    print(f"🌐 Host: {get_host()}")
    print(f"🔌 Port: {get_port()}")
    print(f"🔧 Environment: {os.environ.get('ENVIRONMENT', 'development')}")
    
    # Datenbank-Tabellen erstellen
    try:
        from app.core.database import engine
        from app.models import Base
        Base.metadata.create_all(bind=engine)
        print("✅ Datenbank-Tabellen erstellt")
    except Exception as e:
        print(f"⚠️ Warnung beim Erstellen der Datenbank-Tabellen: {e}")
    
    print("✅ BuildWise Backend erfolgreich gestartet")
    
    yield
    
    # Shutdown
    print("🛑 Beende BuildWise Backend...")

# FastAPI-App erstellen
app = FastAPI(
    title="BuildWise API",
    description="Bauprojektmanagement-API für BuildWise",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS-Konfiguration für Render.com
def get_cors_origins():
    """Hole CORS-Origins basierend auf Environment"""
    # Hole CORS-Origins aus Environment-Variable
    allowed_origins = os.environ.get("ALLOWED_ORIGINS", "")
    
    if allowed_origins:
        # Verwende die Environment-Variable
        origins = [origin.strip() for origin in allowed_origins.split(",") if origin.strip()]
        print(f"🔧 CORS Origins aus Environment: {origins}")
        return origins
    
    # Fallback für Produktion
    if os.environ.get("ENVIRONMENT") == "production":
        origins = [
            "https://frontend-x98q.onrender.com",  # Dein aktuelles Frontend auf Render.com
            "https://buildwise-frontend.onrender.com",
            "https://buildwise-app.onrender.com",
            os.environ.get("FRONTEND_URL", "https://frontend-x98q.onrender.com")
        ]
        print(f"🔧 CORS Origins (Produktion): {origins}")
        return origins
    else:
        # Entwicklungs-Origins
        origins = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8000",
            "http://127.0.0.1:8000"
        ]
        print(f"🔧 CORS Origins (Entwicklung): {origins}")
        return origins

# Erweiterte CORS-Konfiguration für bessere Kompatibilität
def get_cors_config():
    """Erweiterte CORS-Konfiguration"""
    origins = get_cors_origins()
    
    # Füge zusätzliche Origins für bessere Kompatibilität hinzu
    additional_origins = [
        "https://buildwise-backend.onrender.com",
        "https://*.onrender.com",
        "https://*.render.com"
    ]
    
    # Kombiniere alle Origins
    all_origins = origins + additional_origins
    
    print(f"🔧 Finale CORS Origins: {all_origins}")
    return all_origins

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_config(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# API-Router einbinden - mit try-catch für Robustheit
try:
    from app.api import auth
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    print("✅ Auth-Router geladen")
except Exception as e:
    print(f"⚠️ Auth-Router konnte nicht geladen werden: {e}")

try:
    from app.api import users
    app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
    print("✅ Users-Router geladen")
except Exception as e:
    print(f"⚠️ Users-Router konnte nicht geladen werden: {e}")

try:
    from app.api import projects
    app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
    print("✅ Projects-Router geladen")
except Exception as e:
    print(f"⚠️ Projects-Router konnte nicht geladen werden: {e}")

try:
    from app.api import tasks
    app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
    print("✅ Tasks-Router geladen")
except Exception as e:
    print(f"⚠️ Tasks-Router konnte nicht geladen werden: {e}")

try:
    from app.api import documents
    app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
    print("✅ Documents-Router geladen")
except Exception as e:
    print(f"⚠️ Documents-Router konnte nicht geladen werden: {e}")

try:
    from app.api import messages
    app.include_router(messages.router, prefix="/api/v1/messages", tags=["Messages"])
    print("✅ Messages-Router geladen")
except Exception as e:
    print(f"⚠️ Messages-Router konnte nicht geladen werden: {e}")

try:
    from app.api import milestones
    app.include_router(milestones.router, prefix="/api/v1/milestones", tags=["Milestones"])
    print("✅ Milestones-Router geladen")
except Exception as e:
    print(f"⚠️ Milestones-Router konnte nicht geladen werden: {e}")

try:
    from app.api import quotes
    app.include_router(quotes.router, prefix="/api/v1/quotes", tags=["Quotes"])
    print("✅ Quotes-Router geladen")
except Exception as e:
    print(f"⚠️ Quotes-Router konnte nicht geladen werden: {e}")

try:
    from app.api import cost_positions
    app.include_router(cost_positions.router, prefix="/api/v1/cost-positions", tags=["Cost Positions"])
    print("✅ Cost Positions-Router geladen - PostgreSQL-Migration aktiviert")
except Exception as e:
    print(f"⚠️ Cost Positions-Router konnte nicht geladen werden: {e}")

# Health Check Endpoint für Render.com
@app.get("/")
async def root():
    return {
        "message": "BuildWise API läuft!",
        "version": "1.0.0",
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "service": "buildwise-backend"
    }

# Test-Route für Router-Debugging
@app.get("/test-routes")
async def test_routes():
    """Test-Route um zu überprüfen, ob Router geladen werden"""
    return {
        "message": "Test-Route funktioniert",
        "available_routes": [
            "/api/v1/auth",
            "/api/v1/users", 
            "/api/v1/projects",
            "/api/v1/tasks",
            "/api/v1/documents",
            "/api/v1/messages",
            "/api/v1/milestones",
            "/api/v1/quotes",
            "/api/v1/cost-positions"
        ]
    }

# Error Handler für Render.com
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint nicht gefunden",
            "message": "Die angeforderte URL existiert nicht",
            "docs": "/docs"
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Interner Server-Fehler",
            "message": "Ein unerwarteter Fehler ist aufgetreten"
        }
    )

# Nur ausführen, wenn direkt gestartet
if __name__ == "__main__":
    print("🚀 Starte BuildWise Backend lokal...")
    uvicorn.run(
        "app.main:app",
        host=get_host(),
        port=get_port(),
        reload=True if os.environ.get("ENVIRONMENT") == "development" else False,
        log_level="info"
    )
