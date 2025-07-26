from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import os
from dotenv import load_dotenv

load_dotenv()

from .api import api_router
from .core.database import engine
from .models import Base

app = FastAPI(
    title="BuildWise API",
    description="Digitaler Assistent für Immobilienprojekte - Vollständige Backend-API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS-Konfiguration für Netzwerk-Zugriff
allowed_origins_env = os.getenv('ALLOWED_ORIGINS')
if allowed_origins_env:
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(',')]
else:
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "*"  # Temporär für Debugging
    ]

# Debug-Ausgabe für CORS-Konfiguration
print(f"🔧 CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,  # Ändern zu False für "*" Origin
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400
)

# Trusted Host Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # In Produktion spezifische Hosts angeben
)

# Request Timing Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Exception Handler für bessere CORS-Unterstützung
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    print(f"❌ Global Exception Handler: {type(exc).__name__}: {str(exc)}")
    print(f"📍 URL: {request.url}")
    print(f"🔍 Method: {request.method}")
    
    # CORS-Header auch bei Fehlern senden
    response = JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "error_type": type(exc).__name__,
            "message": "Ein interner Serverfehler ist aufgetreten"
        }
    )
    
    # CORS-Header manuell hinzufügen
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response

# API Router einbinden
app.include_router(api_router, prefix="/api/v1")

# Datenbank-Tabellen erstellen
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # SQLite-Optimierungen anwenden
    try:
        from .core.database import optimize_sqlite_connection
        await optimize_sqlite_connection()
    except Exception as e:
        print(f"⚠️ SQLite-Optimierungen konnten nicht angewendet werden: {e}")
    
    # Starte Credit-Scheduler
    try:
        from .core.scheduler import start_credit_scheduler
        await start_credit_scheduler()
        print("✅ Credit-Scheduler gestartet")
    except Exception as e:
        print(f"❌ Fehler beim Starten des Credit-Schedulers: {e}")


@app.on_event("shutdown")
async def on_shutdown():
    # Stoppe Credit-Scheduler
    try:
        from .core.scheduler import stop_credit_scheduler
        await stop_credit_scheduler()
        print("✅ Credit-Scheduler gestoppt")
    except Exception as e:
        print(f"❌ Fehler beim Stoppen des Credit-Schedulers: {e}")

# Health Check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "BuildWise API",
        "version": "1.0.0"
    }

# Root Endpoint
@app.get("/")
async def read_root():
    return {
        "message": "Willkommen bei der BuildWise API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
