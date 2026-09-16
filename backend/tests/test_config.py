"""Tests for the Settings / config module."""

from config import Settings


class TestSettingsDefaults:
    """Default values when no env vars are set."""

    def test_database_url_default(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("REDIS_URL", raising=False)
        monkeypatch.delenv("STORAGE_PATH", raising=False)
        monkeypatch.delenv("APP_ENV", raising=False)
        s = Settings(_env_file=None, _yaml_file="configs/dev.yaml")
        assert (
            s.database_url
            == "postgresql+asyncpg://echotrack:echotrack@localhost:5432/echotrack"
        )

    def test_redis_url_default(self, monkeypatch):
        monkeypatch.delenv("REDIS_URL", raising=False)
        s = Settings(_env_file=None, _yaml_file="configs/dev.yaml")
        assert s.redis_url == ""

    def test_storage_path_default(self, monkeypatch):
        monkeypatch.delenv("STORAGE_PATH", raising=False)
        monkeypatch.delenv("APP_ENV", raising=False)
        s = Settings(_env_file=None, _yaml_file="configs/dev.yaml")
        assert s.storage_path == "./echotrack-storage"

    def test_supabase_defaults(self, monkeypatch):
        for key in ("SUPABASE_URL", "SUPABASE_PUBLISHABLE_KEY", "SUPABASE_SECRET_KEY",
                     "SUPABASE_JWT_SECRET", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY"):
            monkeypatch.delenv(key, raising=False)
        s = Settings(_env_file=None, _yaml_file="configs/dev.yaml")
        assert s.supabase_url == ""
        assert s.supabase_publishable_key == ""
        assert s.supabase_secret_key == ""
        assert s.supabase_jwt_secret == ""


class TestSettingsEnvOverride:
    """Values can be overridden via environment variables."""

    def test_database_url_override(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h:9999/db")
        s = Settings(_env_file=None)
        assert s.database_url == "postgresql+asyncpg://u:p@h:9999/db"

    def test_redis_url_override(self, monkeypatch):
        monkeypatch.setenv("REDIS_URL", "redis://remote:6380")
        s = Settings(_env_file=None)
        assert s.redis_url == "redis://remote:6380"

    def test_supabase_keys_override(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "sb_pub_test")
        monkeypatch.setenv("SUPABASE_SECRET_KEY", "sb_sec_test")
        s = Settings(_env_file=None)
        assert s.supabase_publishable_key == "sb_pub_test"
        assert s.supabase_secret_key == "sb_sec_test"

    def test_supabase_legacy_anon_key_fallback(self, monkeypatch):
        """Legacy SUPABASE_ANON_KEY populates publishable_key when it is empty."""
        monkeypatch.setenv("SUPABASE_ANON_KEY", "sb_anon_legacy")
        s = Settings(_env_file=None)
        assert s.supabase_publishable_key == "sb_anon_legacy"

    def test_supabase_legacy_service_role_key_fallback(self, monkeypatch):
        """Legacy SUPABASE_SERVICE_ROLE_KEY populates secret_key when it is empty."""
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "sb_sr_legacy")
        s = Settings(_env_file=None)
        assert s.supabase_secret_key == "sb_sr_legacy"

    def test_supabase_canonical_wins_over_legacy(self, monkeypatch):
        """When both canonical and legacy keys are set, canonical takes precedence."""
        monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "canonical_pub")
        monkeypatch.setenv("SUPABASE_ANON_KEY", "legacy_anon")
        monkeypatch.setenv("SUPABASE_SECRET_KEY", "canonical_sec")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "legacy_sr")
        s = Settings(_env_file=None)
        assert s.supabase_publishable_key == "canonical_pub"
        assert s.supabase_secret_key == "canonical_sec"

    def test_supabase_url_override(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        s = Settings(_env_file=None)
        assert s.supabase_url == "https://test.supabase.co"

    def test_supabase_jwt_secret_override(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_JWT_SECRET", "super-secret-jwt")
        s = Settings(_env_file=None)
        assert s.supabase_jwt_secret == "super-secret-jwt"

    def test_storage_path_override(self, monkeypatch):
        monkeypatch.setenv("STORAGE_PATH", "/data/storage")
        s = Settings(_env_file=None)
        assert s.storage_path == "/data/storage"

    def test_partial_override(self, monkeypatch):
        """Only the overridden field changes; defaults remain for others."""
        monkeypatch.delenv("REDIS_URL", raising=False)
        monkeypatch.delenv("STORAGE_PATH", raising=False)
        monkeypatch.delenv("APP_ENV", raising=False)
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://override/db")
        s = Settings(_env_file=None, _yaml_file="configs/dev.yaml")
        assert s.database_url == "postgresql+asyncpg://override/db"
        assert s.redis_url == ""
        assert s.storage_path == "./echotrack-storage"
