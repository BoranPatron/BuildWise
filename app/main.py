from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "traceback": traceback.format_exc()
        }
    )

# API Router einbinden
app.include_router(api_router, prefix="/api/v1")

# Datenbank-Tabellen erstellen
#@app.on_event("startup")
#async def on_startup():
#    async with engine.begin() as conn:
#        await conn.run_sync(Base.metadata.create_all)

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
