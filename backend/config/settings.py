"""
Sports AI — Application Settings
Centralized configuration using Pydantic Settings.
"""

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal


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
    llm_provider: Literal["deepseek", "openai", "claude", "grok", "minimax"] = "deepseek"
    deepseek_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    grok_api_key: str = ""
    minimax_api_key: str = ""

    # ── Database ──────────────────────────────────────────────────
    database_url: str = (
        "postgresql+asyncpg://sports_ai:password@localhost:5432/sports_ai"
    )

    # ── Redis ─────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379"

    # ── Application ───────────────────────────────────────────────
    app_env: Literal["development", "staging", "production"] = "development"
    app_port: int = 8000
    model_path: str = "./artifacts/models"
    log_level: str = "INFO"

    # ── Simulation ────────────────────────────────────────────────
    monte_carlo_simulations: int = 50_000
    cache_ttl: int = 3600  # 1 hour

    # ── Admin ─────────────────────────────────────────────────────
    admin_user: str = "admin"
    admin_password: str = ""
    admin_secret_key: str = ""
    admin_token_ttl_seconds: int = 43_200

    # ── CORS ──────────────────────────────────────────────────────
    cors_allowed_origins: list[str] = ["*"]

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

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value):
        if value is None:
            return ["*"]
        if isinstance(value, str):
            raw = value.strip()
            if raw.startswith("[") and raw.endswith("]"):
                import json

                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except Exception:
                    pass
            return [item.strip() for item in raw.split(",") if item.strip()]
        if isinstance(value, (list, tuple, set)):
            return [str(item).strip() for item in value if str(item).strip()]
        return ["*"]

    @model_validator(mode="after")
    def _validate_production_settings(self):
        if not self.is_production:
            return self

        missing = []

        if not self.statpal_access_key and not self.api_football_key:
            missing.append("statpal_access_key/api_football_key")

        llm_key_map = {
            "deepseek": self.deepseek_api_key,
            "openai": self.openai_api_key,
            "claude": self.anthropic_api_key,
            "grok": self.grok_api_key,
            "minimax": self.minimax_api_key,
        }
        if not llm_key_map.get(self.llm_provider):
            missing.append(f"{self.llm_provider}_api_key")

        if not self.database_url or "localhost" in self.database_url:
            missing.append("database_url")
        if not self.redis_url or "localhost" in self.redis_url:
            missing.append("redis_url")
        if not self.admin_password:
            missing.append("admin_password")
        if not self.admin_secret_key:
            missing.append("admin_secret_key")
        if "*" in self.cors_allowed_origins:
            missing.append("cors_allowed_origins")

        if missing:
            raise ValueError(
                "Production settings are incomplete or unsafe: " + ", ".join(sorted(set(missing)))
            )

        return self


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
