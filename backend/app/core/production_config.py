import os
from pydantic_settings import BaseSettings


class ProductionSettings(BaseSettings):
    """Pengaturan Konfigurasi Produksi Tersentralisasi (Centralized Production Settings)."""
    app_env: str = os.getenv("APP_ENV", "production")
    app_name: str = "Fathul Bari Research AI Platform"
    pipeline_version: str = "17.0"
    
    # Infrastructure Endpoints
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./fathul_bari.db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    storage_endpoint: str = os.getenv("STORAGE_ENDPOINT", "s3.fathulbari.id")
    storage_bucket: str = os.getenv("STORAGE_BUCKET", "fathul-bari-corpus-storage")
    
    # Security Boundaries
    jwt_secret: str = os.getenv("JWT_SECRET", "super_secret_production_key_fathul_bari_2026")
    rate_limit_per_min: int = 60
    
    # Observability & Telemetry
    opentelemetry_dsn: str = os.getenv("OPENTELEMETRY_DSN", "https://telemetry.fathulbari.id/v1/traces")
    sentry_dsn: str = os.getenv("SENTRY_DSN", "https://sentry.fathulbari.id/1")

    class Config:
        env_file = ".env"


prod_settings = ProductionSettings()
