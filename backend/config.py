import os
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "dev"
    database_url: str = "postgresql+asyncpg://echotrack:echotrack@localhost:5432/echotrack"
    redis_url: str = ""
    storage_path: str = "./echotrack-storage"

    # Supabase Settings
    supabase_url: str = ""
    supabase_publishable_key: str = ""
    supabase_secret_key: str = ""
    supabase_jwt_secret: str = ""

    # Deprecated aliases — use SUPABASE_PUBLISHABLE_KEY / SUPABASE_SECRET_KEY instead.
    # Kept for backward compatibility with older .env files that use the legacy
    # Supabase "anon key" / "service role key" naming.
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    @model_validator(mode="after")
    def _normalize_legacy_keys(self) -> "Settings":
        """Fold legacy anon/service-role keys into the canonical fields."""
        if not self.supabase_publishable_key and self.supabase_anon_key:
            self.supabase_publishable_key = self.supabase_anon_key
        if not self.supabase_secret_key and self.supabase_service_role_key:
            self.supabase_secret_key = self.supabase_service_role_key
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

