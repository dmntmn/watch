"""Application configuration loaded from environment variables (.env)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application ---
    app_name: str = "Watch"
    debug: bool = False
    cors_origins: list[str] = ["*"]

    # --- Logging (см. src/logging_config.py) ---
    log_level: str = "INFO"  # DEBUG | INFO | WARNING | ERROR | CRITICAL
    log_format: str = "text"  # "text" — человекочитаемый, "json" — для агрегаторов

    # --- PostgreSQL ---
    database_url: str = "postgresql+asyncpg://watch:watch@localhost:5432/watch"

    # --- Redis (pub/sub event bus) ---
    redis_url: str = "redis://localhost:6379/0"
    events_channel: str = "watch:data-changed"

    # --- Keycloak ---
    keycloak_server_url: str = "http://localhost:8080"
    keycloak_realm: str = "watch"
    keycloak_client_id: str = "watch-backend"
    keycloak_client_secret: str = ""
    keycloak_jwks_url: str = ""
    keycloak_issuer: str = ""
    keycloak_audience: str = ""

    # --- SMTP (email notifications to workers) ---
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@watch.local"
    smtp_tls: bool = False
    smtp_starttls: bool = False

    # --- S3 (attachments; MinIO locally) ---
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "watch-attachments"
    s3_region: str = "us-east-1"
    s3_use_ssl: bool = False

    @property
    def keycloak_issuer_url(self) -> str:
        return self.keycloak_issuer or f"{self.keycloak_server_url}/realms/{self.keycloak_realm}"

    @property
    def keycloak_jwks_uri(self) -> str:
        return (
            self.keycloak_jwks_url
            or f"{self.keycloak_server_url}/realms/{self.keycloak_realm}/protocol/openid-connect/certs"
        )

    @property
    def keycloak_aud(self) -> str:
        return self.keycloak_audience or self.keycloak_client_id


@lru_cache
def get_settings() -> Settings:
    return Settings()