"""Runtime configuration for the Smart Pantry API.

All deploy-specific values come from environment variables so the same build can
run locally, in a preview environment, or in production without source edits.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _csv_env(name: str, default: str = "") -> tuple[str, ...]:
    value = os.getenv(name, default)
    return tuple(item.strip().rstrip("/") for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    environment: str
    log_level: str
    allowed_origins: tuple[str, ...]
    allow_vercel_previews: bool

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    default_origins = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "https://smart-pantry-kappa.vercel.app,"
        "https://smart-pantry-capstone.vercel.app"
    )
    return Settings(
        app_name="Smart Pantry 2.0 API",
        app_version=os.getenv("APP_VERSION", "2.0.0-phase18"),
        environment=os.getenv("APP_ENV", "development"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        allowed_origins=_csv_env("ALLOWED_ORIGINS", default_origins),
        allow_vercel_previews=os.getenv("ALLOW_VERCEL_PREVIEWS", "true").lower()
        in {"1", "true", "yes", "on"},
    )


def origin_is_allowed(origin: str | None, settings: Settings | None = None) -> bool:
    current = settings or get_settings()
    if not origin:
        return False
    normalized = origin.rstrip("/")
    if normalized in current.allowed_origins:
        return True
    return (
        current.allow_vercel_previews
        and normalized.startswith("https://")
        and normalized.endswith(".vercel.app")
    )


def build_health_payload(settings: Settings | None = None) -> dict[str, str]:
    current = settings or get_settings()
    return {
        "status": "ok",
        "service": current.app_name,
        "version": current.app_version,
        "environment": current.environment,
    }


def public_error_detail(public_message: str, exc: Exception, settings: Settings | None = None) -> str:
    current = settings or get_settings()
    if current.is_production:
        return public_message
    return f"{public_message}: {type(exc).__name__}: {exc}"
