from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Sports Media Protection - Layer 3 and 4"
    api_prefix: str = "/api/v1"

    blockchain_network: str = "polygon_mumbai"
    blockchain_tx_prefix: str = "0x"
    blockchain_salt: str = "sports_media_protection_salt"

    database_path: str = "./data/content_registry.db"
    ai_model_version: str = "v1.0"
    registered_by: str = "layer3_4_service"
    enable_google_ai: bool = True
    google_ai_timeout_seconds: float = 2.0
    google_api_key: str | None = None
    google_cloud_project: str | None = None
    google_cloud_location: str = "us-central1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
