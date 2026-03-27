from urllib.parse import urlsplit

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "tabletki-backend"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/tabletki"
    redis_url: str = "redis://localhost:6379/0"
    geoapify_api_key: str = ""
    openrouter_api_key: str = ""
    openrouter_model: str = ""
    openrouter_http_referer: str = "http://127.0.0.1:3000"
    openrouter_title: str = "tabletki-mvp"
    frontend_origin: str = "http://127.0.0.1:3000"
    default_city_id: str = "1"
    default_area_id: str = "0"
    kafka_bootstrap_servers: str = "localhost:9092"
    log_level: str = "INFO"
    geocode_refresh_timezone: str = "Europe/Moscow"
    geocode_refresh_window_start: str = "23:30"
    geocode_refresh_window_end: str = "06:00"
    geocode_refresh_interval_hours: int = 72
    geocode_unresolved_refresh_interval_hours: int = 72
    geocode_refresh_batch_size: int = 500
    geocode_refresh_loop_interval_seconds: int = 900
    geocode_provider_cooldown_seconds: int = 600

    def allowed_frontend_origins(self) -> list[str]:
        origins = {self.frontend_origin}
        parsed = urlsplit(self.frontend_origin)
        if parsed.hostname == "127.0.0.1":
            origins.add(f"{parsed.scheme}://localhost:{parsed.port}")
        elif parsed.hostname == "localhost":
            origins.add(f"{parsed.scheme}://127.0.0.1:{parsed.port}")
        return sorted(origins)
