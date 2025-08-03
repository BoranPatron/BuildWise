from fastapi import FastAPI, Request, Body, Depends, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
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
        # Netzwerk-Zugriff für mobile Geräte
        "http://192.168.1.65:5173",
        "http://192.168.1.65:3000",
        "http://192.168.1.65:5174"
    ]

# Debug-Ausgabe für CORS-Konfiguration
print(f"🔧 CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,  # Aktiviert für OAuth-Flows
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

# Static Files für Storage
from fastapi.staticfiles import StaticFiles
import os

# Erstelle Storage-Verzeichnis falls nicht vorhanden
storage_path = "storage"
if not os.path.exists(storage_path):
    os.makedirs(storage_path)

# Mount static files für Storage
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

# Authentifizierte Datei-Serving Route
from fastapi import Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from .api.deps import get_current_user
from .models import User
from .core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import os

@app.get("/api/v1/files/serve/{file_path:path}")
async def serve_authenticated_file(
    file_path: str,
    token: str = Query(..., description="JWT Token für Authentifizierung"),
    db: AsyncSession = Depends(get_db)
):
    """Stellt Dateien mit Token-Authentifizierung bereit"""
    try:
        print(f"🔍 serve_authenticated_file: Token erhalten: {token[:50]}..." if token else "🔍 serve_authenticated_file: Kein Token")
        
        # Token validieren
        from .core.security import decode_access_token
        payload = decode_access_token(token)
        
        if not payload:
            print(f"❌ serve_authenticated_file: Token konnte nicht decodiert werden")
            raise HTTPException(status_code=401, detail="Ungültiger Token")
        
        print(f"🔍 serve_authenticated_file: Token payload: {payload}")
        
        # Benutzer-ID aus Token extrahieren
        user_id = payload.get("sub")
        if not user_id:
            print(f"❌ serve_authenticated_file: Keine user_id im Token gefunden")
            raise HTTPException(status_code=401, detail="Ungültiger Token - keine Benutzer-ID")
        
        # Benutzer aus Datenbank laden
        from sqlalchemy import select
        from .models import User
        
        # Versuche zuerst mit E-Mail
        result = await db.execute(select(User).where(User.email == user_id))
        user = result.scalar_one_or_none()
        
        # Falls nicht gefunden, versuche mit ID
        if not user and user_id.isdigit():
            result = await db.execute(select(User).where(User.id == int(user_id)))
            user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ serve_authenticated_file: Benutzer nicht gefunden für ID/E-Mail: {user_id}")
            raise HTTPException(status_code=401, detail="Benutzer nicht gefunden")
        
        print(f"✅ serve_authenticated_file: Benutzer authentifiziert: {user.id}, {user.email}")
        
        # Vollständiger Pfad zur Datei
        full_path = os.path.join("storage", file_path)
        
        # Sicherheitsprüfung: Stelle sicher, dass der Pfad innerhalb des storage-Verzeichnisses liegt
        if not os.path.abspath(full_path).startswith(os.path.abspath("storage")):
            print(f"❌ serve_authenticated_file: Zugriff verweigert für Pfad: {full_path}")
            raise HTTPException(status_code=403, detail="Zugriff verweigert")
        
        # Prüfe ob die Datei existiert
        if not os.path.exists(full_path):
            print(f"❌ serve_authenticated_file: Datei nicht gefunden: {full_path}")
            raise HTTPException(status_code=404, detail="Datei nicht gefunden")
        
        # Bestimme den MIME-Type
        import mimetypes
        mime_type, _ = mimetypes.guess_type(full_path)
        if mime_type is None:
            mime_type = "application/octet-stream"
        
        print(f"✅ serve_authenticated_file: Datei erfolgreich bereitgestellt: {full_path}")
        
        # Für Bilder: Inline-Anzeige im Browser statt Download
        is_image = mime_type and mime_type.startswith('image/')
        
        if is_image:
            # Bilder inline anzeigen
            return FileResponse(
                path=full_path,
                media_type=mime_type,
                headers={"Content-Disposition": "inline"}
            )
        else:
            # Andere Dateien als Download
            return FileResponse(
                path=full_path,
                media_type=mime_type,
                filename=os.path.basename(full_path)
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ serve_authenticated_file: Unerwarteter Fehler: {str(e)}")
        import traceback
        print(f"❌ serve_authenticated_file: Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=401, detail="Authentifizierung fehlgeschlagen")

# Static Files für hochgeladene Dokumente (nur für Entwicklung)
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

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

# Debug Endpoint für Progress Updates
@app.post("/api/v1/debug/progress")
async def debug_progress_simple(data: dict = Body(...)):
    """Einfacher Debug-Endpoint ohne Dependencies"""
    print(f"🎯 [MAIN DEBUG] Endpoint erreicht!")
    print(f"🎯 [MAIN DEBUG] Received Data: {data}")
    return {"status": "received", "data": data}

# Debug Endpoint für Attachments
@app.post("/api/v1/debug/attachment")
async def debug_attachment_simple(file: UploadFile = File(..., alias="file")):
    """Einfacher Debug-Endpoint für Attachments"""
    print(f"🎯 [MAIN DEBUG ATTACHMENT] Endpoint erreicht!")
    print(f"🎯 [MAIN DEBUG ATTACHMENT] File: {file.filename}")
    print(f"🎯 [MAIN DEBUG ATTACHMENT] Content-Type: {file.content_type}")
    print(f"🎯 [MAIN DEBUG ATTACHMENT] Size: {file.size}")
    
    # Lese den Inhalt für Debug-Zwecke
    content = await file.read()
    print(f"🎯 [MAIN DEBUG ATTACHMENT] Content length: {len(content)} bytes")
    print(f"🎯 [MAIN DEBUG ATTACHMENT] First 100 bytes: {content[:100]}")
    
    return {"status": "received", "filename": file.filename, "content_type": file.content_type, "size": len(content)}

# Debug Endpoint für Request-Details
@app.post("/api/v1/debug/request")
async def debug_request_simple(request: Request):
    """Debug-Endpoint für Request-Details"""
    print(f"🎯 [MAIN DEBUG REQUEST] Endpoint erreicht!")
    print(f"🎯 [MAIN DEBUG REQUEST] Method: {request.method}")
    print(f"🎯 [MAIN DEBUG REQUEST] URL: {request.url}")
    print(f"🎯 [MAIN DEBUG REQUEST] Content-Type: {request.headers.get('content-type', 'NOT SET')}")
    print(f"🎯 [MAIN DEBUG REQUEST] Headers: {dict(request.headers)}")
    
    # Lese den Body
    body = await request.body()
    print(f"🎯 [MAIN DEBUG REQUEST] Body length: {len(body)} bytes")
    print(f"🎯 [MAIN DEBUG REQUEST] Body preview: {body[:200]}")
    
    # Prüfe ob es Multipart-FormData ist
    content_type = request.headers.get('content-type', '')
    if 'multipart/form-data' in content_type:
        print(f"🎯 [MAIN DEBUG REQUEST] ✅ Multipart-FormData erkannt!")
    else:
        print(f"🎯 [MAIN DEBUG REQUEST] ❌ Kein Multipart-FormData: {content_type}")
    
    return {"status": "received", "method": request.method, "body_length": len(body), "content_type": content_type}

# Root Endpoint
@app.get("/")
async def read_root():
    return {
        "message": "Willkommen bei der BuildWise API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
