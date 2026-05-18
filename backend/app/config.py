"""
Application configuration using Pydantic BaseSettings.
Type-safe, validated configuration with .env support configured for PostgreSQL.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "AntiFarm - Field Force Intelligence"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ── PostgreSQL ───────────────────────────────────────
    # Replaced MONGO_URI and MONGO_DB_NAME with standard, validated relational connection parameters
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:password@localhost:5432/antifarm",
        description="Async PostgreSQL connection string using the psycopg driver schema"
    )

    # ── CORS ─────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    # ── Auth ─────────────────────────────────────────────
    SECRET_KEY: str = "dev-secret-change-in-production-antifarm-2026"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # ── External APIs ────────────────────────────────────
    WEATHER_API_KEY: Optional[str] = None
    WEATHER_API_URL: str = "https://api.openweathermap.org/data/2.5"

    # ── Data Paths ───────────────────────────────────────
    DATA_DIR: str = "../data"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton — avoids re-parsing .env on every call."""
    return Settings()