"""Validated local warehouse settings."""

from __future__ import annotations

from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WarehouseSettings(BaseSettings):
    """PostgreSQL settings with compose-compatible development defaults."""

    model_config = SettingsConfigDict(env_prefix="BANKING_POSTGRES_", extra="ignore")

    host: str = "localhost"
    port: int = Field(default=55433, ge=1, le=65535)
    db: str = "banking"
    user: str = "banking"
    password: str = "banking_local_only"

    @property
    def dsn(self) -> str:
        """Return a safely escaped psycopg/dlt connection URL."""
        user = quote_plus(self.user)
        password = quote_plus(self.password)
        db = quote_plus(self.db)
        return f"postgresql://{user}:{password}@{self.host}:{self.port}/{db}"
