import os
from functools import lru_cache


class Settings:
    """Application configuration loaded from environment variables."""

    def __init__(self):
        # Verwende os.environ für alle Konfigurationswerte
        self.db_host = os.environ.get("DB_HOST", "localhost")
        self.db_port = int(os.environ.get("DB_PORT", "5432"))
        self.db_name = os.environ.get("DB_NAME", "buildwise")
        self.db_user = os.environ.get("DB_USER", "postgres")
        self.db_password = os.environ.get("DB_PASSWORD", "password")
        self.jwt_secret_key = os.environ.get("JWT_SECRET_KEY", "your_super_secret_jwt_key_here")
        self.jwt_algorithm = os.environ.get("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


@lru_cache()
def get_settings() -> Settings:
    return Settings()
