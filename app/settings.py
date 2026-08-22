"""Configurações que podem ser alteradas por variáveis de ambiente."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Reúne os endereços dos serviços e os tempos da demonstração."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://pagamentos:pagamentos@localhost:5432/pagamentos"
    redis_url: str = "redis://localhost:6379/0"
    payment_delay_seconds: int = Field(default=30, ge=1, le=300)
    payment_cache_ttl_seconds: int = Field(default=15, ge=1, le=3600)


settings = Settings()
