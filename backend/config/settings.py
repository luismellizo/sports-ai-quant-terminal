"""
Sports AI — Application Settings
Centralized configuration using Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal
import os


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # ── Statpal Soccer API ───────────────────────────────────────
    statpal_access_key: str = ""
    statpal_base_url: str = "https://statpal.io/api/v2"
    statpal_sport: str = "soccer"

    # ── API-Football ──────────────────────────────────────────────
    # Legacy fallback keys kept for backward compatibility.
    api_football_key: str = ""
    api_football_base_url: str = "https://v3.football.api-sports.io"

    # ── LLM ───────────────────────────────────────────────────────
    llm_provider: Literal["deepseek", "openai", "claude", "grok"] = "deepseek"
    deepseek_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    grok_api_key: str = ""

    # ── Database ──────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://sports_ai:password@localhost:5432/sports_ai"

    # ── Redis ─────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379"

    # ── Application ───────────────────────────────────────────────
    app_env: Literal["development", "staging", "production"] = "development"
    app_port: int = 8000
    model_path: str = "./models"
    log_level: str = "INFO"

    # ── Simulation ────────────────────────────────────────────────
    monte_carlo_simulations: int = 50_000
    cache_ttl: int = 3600  # 1 hour

    # ── Admin ─────────────────────────────────────────────────────
    admin_user: str = "admin"
    admin_password: str = "Masflow2@"
    admin_secret_key: str = "sports-ai-admin-secret-key-2026"

    # ── Concurrency ───────────────────────────────────────────────
    max_concurrent_pipelines: int = 15

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
