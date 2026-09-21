"""
Configurações centrais do Hellux.

Todas as variáveis sensíveis (banco, segredos, etc.) vêm de variáveis de
ambiente / arquivo .env, nunca hardcoded no código-fonte.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Aplicação
    APP_NAME: str = "Hellux"
    APP_VERSION: str = "1.2.0"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = True

    # Banco de dados
    DATABASE_URL: str = (
        "postgresql+psycopg2://hellux:hellux@localhost:5432/hellux"
    )

    # CORS - endereços do frontend autorizados a consumir a API
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Segurança (usado a partir do Sprint 12 - Autenticação)
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 horas

    # Importação de Laudo (extração assistida por IA - ver LaudoImportService)
    ANTHROPIC_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Retorna a instância única (cacheada) das configurações."""
    return Settings()
