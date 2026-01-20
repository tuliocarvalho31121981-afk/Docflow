# app/core/config.py
"""
Core - Config
Configurações da aplicação via variáveis de ambiente.
"""
from functools import lru_cache
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação."""

    # App
    app_env: str = "development"
    app_debug: bool = True
    app_secret_key: str = "change-me-in-production-use-random-string"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/v1"

    # Supabase
    supabase_url: str
    supabase_key: str  # anon key
    supabase_service_key: str  # service_role key
    supabase_db_url: Optional[str] = None  # ← NOVO: Connection string para PostgresSaver

    # JWT (usado apenas para validações extras, auth principal é via Supabase)
    jwt_secret: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # 1 hora

    # CORS
    cors_origins: str = "*"

    # Storage
    storage_bucket: str = "documentos"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # LLM Providers
    llm_provider: str = "groq"  # groq | deepseek | openai | openrouter
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.1-70b-versatile"
    groq_model_whisper: str = "whisper-large-v3"  # Modelo para transcrição de áudio
    deepseek_api_key: Optional[str] = None
    deepseek_model: str = "deepseek-chat"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-sonnet-4.5"

    # Clinica padrão para desenvolvimento (sem auth)
    default_clinica_id: Optional[str] = None

    # Webhook
    webhook_secret: Optional[str] = None

    # WhatsApp / Evolution API
    evolution_api_url: Optional[str] = None
    evolution_api_key: Optional[str] = None
    evolution_instance: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignora variáveis extras no .env
    )

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Valida configurações críticas em produção."""
        if self.app_env == "production":
            # JWT secret não pode ser o default em produção
            if self.jwt_secret == "CHANGE_ME_IN_PRODUCTION":
                raise ValueError(
                    "JWT_SECRET deve ser configurado em produção! "
                    "Use uma string aleatória de pelo menos 32 caracteres."
                )

            # App secret key não pode ser default
            if self.app_secret_key == "change-me-in-production-use-random-string":
                raise ValueError(
                    "APP_SECRET_KEY deve ser configurado em produção!"
                )

            # Aviso sobre CORS aberto em produção
            if self.cors_origins == "*":
                import warnings
                warnings.warn(
                    "CORS_ORIGINS está configurado como '*' em produção. "
                    "Considere restringir para domínios específicos.",
                    UserWarning
                )

            # Debug deve estar desabilitado em produção
            if self.app_debug:
                import warnings
                warnings.warn(
                    "APP_DEBUG está habilitado em produção. "
                    "Isso pode expor informações sensíveis.",
                    UserWarning
                )

        return self

    @property
    def cors_origins_list(self) -> list[str]:
        """Retorna lista de origens CORS."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        """Verifica se está em produção."""
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Retorna instância cacheada das configurações."""
    return Settings()


# Instância global
settings = get_settings()
