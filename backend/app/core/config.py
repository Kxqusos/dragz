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
    yandex_geocoder_api_key: str = ""
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
    geocode_provider_daily_request_limit: int = 1000
    geocode_provider_daily_safety_buffer: int = 10
    jwt_secret: str = "change-me-jwt-secret-change-me-jwt-secret"
    jwt_algorithm: str = "HS256"
    auth_access_token_ttl_minutes: int = 15
    auth_refresh_token_ttl_days: int = 30
    auth_cookie_secure: bool = False
    auth_cookie_domain: str = ""
    auth_bootstrap_admin_emails: str = ""
    auth_code_ttl_minutes: int = 15
    auth_code_resend_cooldown_seconds: int = 60
    auth_verification_code_resend_cooldown_seconds: int = 60
    auth_password_reset_code_cooldown_seconds: int = 300
    auth_code_max_attempts: int = 5
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@example.com"
    smtp_from_name: str = "tabletki.ru"
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    debug_hash_salt: str = "change-me-debug-salt-change-me-debug-salt"
    debug_retention_days: int = 30
    history_retention_days: int = 180
    site_name: str = "Драгз.рф"
    site_support_email: str = "support@example.com"
    site_support_url: str = ""
    feature_registration_enabled: bool = True
    feature_ai_consult_enabled: bool = True

    def allowed_frontend_origins(self) -> list[str]:
        origins = {self.frontend_origin}
        parsed = urlsplit(self.frontend_origin)
        if parsed.hostname == "127.0.0.1":
            origins.add(f"{parsed.scheme}://localhost:{parsed.port}")
        elif parsed.hostname == "localhost":
            origins.add(f"{parsed.scheme}://127.0.0.1:{parsed.port}")
        return sorted(origins)

    def bootstrap_admin_emails(self) -> set[str]:
        return {
            email.strip().lower()
            for email in self.auth_bootstrap_admin_emails.split(",")
            if email.strip()
        }
