from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Datenbank
    database_url: str = "sqlite:///./buildwise.db"
    
    # JWT
    secret_key: str = "your-secret-key-here-change-in-production"
    jwt_secret_key: str = "your-secret-key-here-change-in-production"  # Alias für Kompatibilität
    algorithm: str = "HS256"
    jwt_algorithm: str = "HS256"  # Alias für Kompatibilität
    access_token_expire_minutes: int = 30
    
    # CORS
    cors_origins: list = ["http://localhost:5173", "http://localhost:3000"]
    
    # Google OAuth
    google_client_id: str = "1039127200110-vav094cta93qmtleivdj63un5dne17eb.apps.googleusercontent.com"
    google_client_secret: str = "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"
    google_redirect_uri: str = "http://localhost:5173/auth/google/callback"
    
    # Microsoft OAuth (optional)
    microsoft_client_id: Optional[str] = None
    microsoft_client_secret: Optional[str] = None
    microsoft_redirect_uri: str = "http://localhost:5173/auth/microsoft/callback"
    
    # Sicherheit
    bcrypt_rounds: int = 12
    max_login_attempts: int = 5
    account_lockout_duration_minutes: int = 30
    
    # DSGVO
    data_retention_days: int = 730  # 2 Jahre
    consent_required: bool = True
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignoriere unbekannte Felder


# Erstelle eine globale Settings-Instanz
settings = Settings()
