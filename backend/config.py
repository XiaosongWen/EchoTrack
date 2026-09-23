import os
from typing import List
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "dev"
    database_url: str = "postgresql+asyncpg://echotrack:echotrack@localhost:5432/echotrack"
    redis_url: str = ""
    storage_path: str = "./echotrack-storage"
    # CORS — comma-separated list of allowed origins.
    # In Cloud Run set CORS_ORIGINS=https://your-project.pages.dev,https://yourdomain.com
    cors_origins: List[str] = []

    # Supabase Settings
    supabase_url: str = ""
    supabase_publishable_key: str = ""
    supabase_secret_key: str = ""

    # Deprecated aliases — use SUPABASE_PUBLISHABLE_KEY / SUPABASE_SECRET_KEY instead.
    # Kept for backward compatibility with older .env files that use the legacy
    # Supabase "anon key" / "service role key" naming.
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    _DEV_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    @model_validator(mode="after")
    def _normalize(self) -> "Settings":
        """Fold legacy anon/service-role keys into the canonical fields,
        and ensure dev localhost origins are always present in cors_origins."""
        if not self.supabase_publishable_key and self.supabase_anon_key:
            self.supabase_publishable_key = self.supabase_anon_key
        if not self.supabase_secret_key and self.supabase_service_role_key:
            self.supabase_secret_key = self.supabase_service_role_key
        # Always include dev localhost origins so local dev works out-of-the-box.
        merged = list(dict.fromkeys(self._DEV_ORIGINS + self.cors_origins))
        self.cors_origins = merged
        return self

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


_env = os.environ.get("APP_ENV", "dev")
_yaml_path = os.path.join(os.path.dirname(__file__), "configs", f"{_env}.yaml")

if os.path.exists(_yaml_path):
    settings = Settings(_yaml_file=_yaml_path)
else:
    settings = Settings()

