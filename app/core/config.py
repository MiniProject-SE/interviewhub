"""Central configuration, loaded from environment variables.

All tunables live here so that modules never read os.environ directly
(single place to audit for security review).
"""
import os
from dataclasses import dataclass, field


def _bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = "InterviewHub"
    version: str = "1.0.0"
    database_url: str = field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./interviewhub.db")
    )
    jwt_secret: str = field(
        default_factory=lambda: os.getenv("JWT_SECRET", "dev-only-change-me-in-production-0123456789")
    )
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = field(
        default_factory=lambda: int(os.getenv("JWT_EXPIRY_MINUTES", "120"))
    )
    # New experiences need moderator approval unless this is switched off.
    require_moderation: bool = field(
        default_factory=lambda: _bool(os.getenv("REQUIRE_MODERATION", "true"))
    )
    cors_origins: tuple = field(
        default_factory=lambda: tuple(
            o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()
        )
    )


settings = Settings()
