"""Application configuration management."""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    # App settings
    app_name: str = "SmsManager"
    debug: bool = False

    # Database settings
    database_path: str = os.getenv("DATABASE_PATH", "data/sqlite.db")

    @property
    def database_url(self) -> str:
        """Get SQLite database URL."""
        return f"sqlite:///{self.database_path}"

    @property
    def database_file(self) -> str:
        """Get absolute path to database file."""
        return str(Path(__file__).parent.parent / self.database_path)

    # JWT settings
    secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # TOTP settings
    totp_issuer: str = "SmsManager"

    # CORS settings
    cors_origins: list = ["http://localhost:5173", "http://localhost:3000", "*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
