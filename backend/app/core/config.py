"""Configuração central da aplicação, carregada de variáveis de ambiente."""
from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_SECRETS = {"dev-secret-change-me", "dev-pix-webhook-secret"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Aplicação
    PROJECT_NAME: str = "EconoFácil API"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # Segurança
    SECRET_KEY: str = "dev-secret-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    EMAIL_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # Banco de dados
    DATABASE_URL: str = "postgresql+asyncpg://econofacil:econofacil@localhost:5432/econofacil"

    # 2FA
    TOTP_ISSUER: str = "EconoFácil"

    # Noor (otimização de cestas)
    NOOR_SOLVER_ENABLED: bool = True
    NOOR_FORCE_HEURISTIC: bool = False

    # Pagamentos (PIX)
    PIX_KEY: str = "pagamentos@econofacil.com.br"
    PIX_CHARGE_TTL_SECONDS: int = 3600
    PIX_WEBHOOK_SECRET: str = "dev-pix-webhook-secret"

    # Agendador de expirações (RN-021): carrinhos, promoções e cobranças Pix
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_INTERVAL_SECONDS: int = 60

    # Modo demonstração local: habilita o botão "Simular pagamento" (PIX é simulado)
    LOCAL_DEMO: bool = False

    # LGPD
    TERMS_VERSION: str = "2025.1"

    @model_validator(mode="after")
    def _reject_default_secrets(self):
        """Fora do modo demonstração (e dos testes), recusa iniciar com segredos padrão."""
        if self.LOCAL_DEMO or self.ENVIRONMENT == "test":
            return self
        padrao = [
            nome for nome, valor in (
                ("SECRET_KEY", self.SECRET_KEY),
                ("PIX_WEBHOOK_SECRET", self.PIX_WEBHOOK_SECRET),
            ) if valor in _DEFAULT_SECRETS
        ]
        if padrao:
            raise ValueError(
                f"{', '.join(padrao)} está com o valor padrão. Defina valores próprios no .env "
                "(gere com: python -c \"import secrets; print(secrets.token_urlsafe(64))\") "
                "ou use LOCAL_DEMO=true apenas para demonstração local."
            )
        return self

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
