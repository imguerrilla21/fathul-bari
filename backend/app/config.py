from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Fathul Bari Research API"
    app_env: str = "development"
    database_url: str

    ahmad_sanusi_base_url: str = "https://api.ahmadsanusi.com"
    ahmad_sanusi_api_key: str

    sync_delay_seconds: float = 0.25
    sync_max_retries: int = 4

    # AI / RAG Configuration
    ai_provider: str = "auto"  # "auto", "gemini", "openai", "builtin"
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    ai_model_name: str = "gemini-1.5-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()

