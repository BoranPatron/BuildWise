import os
from typing import Optional, List

class Settings:
    # Datenbank-Konfiguration
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./buildwise.db")
    DATABASE_PASSWORD: Optional[str] = os.environ.get("DATABASE_PASSWORD")
    
    # JWT-Konfiguration
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "your_super_secret_jwt_key_here_make_it_long_and_random_at_least_32_characters")
    JWT_ALGORITHM: str = os.environ.get("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Anwendungseinstellungen
    DEBUG: bool = os.environ.get("DEBUG", "True").lower() == "true"
    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "development")
    API_VERSION: str = os.environ.get("API_VERSION", "v1")
    APP_NAME: str = os.environ.get("APP_NAME", "BuildWise")
    APP_VERSION: str = os.environ.get("APP_VERSION", "1.0.0")
    TIMEZONE: str = os.environ.get("TIMEZONE", "Europe/Berlin")
    LANGUAGE: str = os.environ.get("LANGUAGE", "de")
    
    # Server-Konfiguration
    HOST: str = os.environ.get("HOST", "0.0.0.0")
    PORT: int = int(os.environ.get("PORT", "8000"))
    
    # CORS-Konfiguration
    ALLOWED_ORIGINS: List[str] = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173").split(",")
    ALLOWED_METHODS: List[str] = os.environ.get("ALLOWED_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(",")
    ALLOWED_HEADERS: List[str] = os.environ.get("ALLOWED_HEADERS", "Content-Type,Authorization,X-Requested-With").split(",")
    ALLOW_CREDENTIALS: bool = os.environ.get("ALLOW_CREDENTIALS", "True").lower() == "true"
    
    # Datei-Upload-Konfiguration
    MAX_FILE_SIZE: int = int(os.environ.get("MAX_FILE_SIZE", "10485760"))  # 10MB
    ALLOWED_FILE_TYPES: List[str] = os.environ.get("ALLOWED_FILE_TYPES", "pdf,jpg,jpeg,png,docx,xlsx,zip,rar").split(",")
    UPLOAD_PATH: str = os.environ.get("UPLOAD_PATH", "storage/uploads")

def get_settings() -> Settings:
    return Settings()

# Globale Settings-Instanz
settings = get_settings()
