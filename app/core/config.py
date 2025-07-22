from pydantic_settings import BaseSettings
from typing import Optional, Literal
import os
import json
from pathlib import Path


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
    
    # Microsoft OAuth
    microsoft_client_id: Optional[str] = None
    microsoft_client_secret: Optional[str] = None
    microsoft_redirect_uri: str = "http://localhost:5173/auth/microsoft/callback"
    
    # BuildWise Fee Configuration
    buildwise_fee_percentage: float = 0.0
    buildwise_fee_phase: Literal["beta", "production"] = "beta"
    buildwise_fee_enabled: bool = True
    
    # Environment Mode
    environment_mode: Literal["beta", "production"] = "beta"
    
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_environment_config()
    
    def _load_environment_config(self):
        """Lädt die Environment-Konfiguration aus der JSON-Datei."""
        config_file = Path("environment_config.json")
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                # Aktualisiere BuildWise Fee Einstellungen
                if "buildwise_fee_percentage" in config:
                    self.buildwise_fee_percentage = config["buildwise_fee_percentage"]
                if "buildwise_fee_phase" in config:
                    self.buildwise_fee_phase = config["buildwise_fee_phase"]
                if "buildwise_fee_enabled" in config:
                    self.buildwise_fee_enabled = config["buildwise_fee_enabled"]
                if "environment_mode" in config:
                    self.environment_mode = config["environment_mode"]
                    
            except Exception as e:
                print(f"⚠️  Warnung: Konnte environment_config.json nicht laden: {e}")
    
    def get_fee_percentage(self) -> float:
        """Gibt den aktuellen Gebühren-Prozentsatz basierend auf der Phase zurück."""
        # Lade die aktuelle Konfiguration dynamisch
        self._load_environment_config()
        
        if self.environment_mode == "beta":
            return 0.0
        elif self.environment_mode == "production":
            return 4.7
        return self.buildwise_fee_percentage
    
    def is_beta_mode(self) -> bool:
        """Prüft, ob das System im Beta-Modus läuft."""
        return self.environment_mode == "beta"
    
    def is_production_mode(self) -> bool:
        """Prüft, ob das System im Production-Modus läuft."""
        return self.environment_mode == "production"


# Erstelle eine globale Settings-Instanz
settings = Settings()

def get_settings() -> Settings:
    """Gibt eine frische Settings-Instanz zurück, die die aktuelle Konfiguration lädt."""
    return Settings()

def get_fee_percentage() -> float:
    """Gibt den aktuellen Gebühren-Prozentsatz dynamisch zurück."""
    current_settings = get_settings()
    return current_settings.get_fee_percentage()

def is_beta_mode() -> bool:
    """Prüft dynamisch, ob das System im Beta-Modus läuft."""
    current_settings = get_settings()
    return current_settings.is_beta_mode()

def is_production_mode() -> bool:
    """Prüft dynamisch, ob das System im Production-Modus läuft."""
    current_settings = get_settings()
    return current_settings.is_production_mode()
