from functools import lru_cache
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Database settings with defaults for SQLite
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "buildwise.db"  # Default to SQLite file
    db_user: str = "sqlite"
    db_password: str = "sqlite"

    # JWT settings
    jwt_secret_key: str = "your_super_secret_jwt_key_here_make_it_long_and_random_at_least_32_characters"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    @property
    def database_url(self) -> str:
        """Konstruiert die Database-URL aus den einzelnen Feldern"""
        # Für SQLite verwenden wir eine lokale Datei
        if self.db_name.endswith(".db") or self.db_host == "localhost":
            return f"sqlite+aiosqlite:///./{self.db_name}"
        # Für andere Datenbanken (PostgreSQL, MySQL, etc.)
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
