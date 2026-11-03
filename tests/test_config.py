"""Tests para app.core.config module."""

from app.core.config import Settings, settings


class TestSettings:
    """Tests para la clase de configuración Settings."""

    def test_settings_loads_from_env(self, setup_env):
        """Test que Settings carga todos los campos requeridos desde el environment."""
        s = Settings()
        assert s.SUPABASE_URL == "https://test.supabase.co"
        assert s.SUPABASE_KEY == "test_key_123"
        assert s.RESEND_API_KEY == "re_test_123"
        assert s.EMAIL_SENDER == "onboarding@resend.dev"
        assert s.GEMINI_API_KEY == "test_gemini_key"
        assert s.GEMINI_MODEL == "gemini-2.5-flash"

    def test_extra_fields_ignored(self, monkeypatch):
        """Test que extra='ignore' permite campos desconocidos sin error."""
        import os

        for key in ["EMAIL_RECIPIENT", "GITHUB_PAT"]:
            os.environ.pop(key, None)

        monkeypatch.setenv("EMAIL_RECIPIENT", "unused@example.com")
        monkeypatch.setenv("GITHUB_PAT", "ghp_fake_token")
        # No debe lanzar excepción
        s = Settings()
        assert s.SUPABASE_URL == "https://test.supabase.co"

    def test_gemini_model_default(self, monkeypatch):
        """Test GEMINI_MODEL tiene valor por defecto."""
        monkeypatch.delenv("GEMINI_MODEL", raising=False)
        s = Settings()
        assert s.GEMINI_MODEL == "gemini-2.5-flash"


class TestSettingsSingleton:
    """Tests para la instancia global de settings."""

    def test_global_settings_exists(self):
        """Test que la instancia global de settings existe."""
        assert settings is not None
        assert isinstance(settings, Settings)

    def test_global_settings_has_required_attrs(self, setup_env):
        """Test que la settings global tiene todos los atributos requeridos."""
        assert hasattr(settings, "SUPABASE_URL")
        assert hasattr(settings, "SUPABASE_KEY")
        assert hasattr(settings, "RESEND_API_KEY")
        assert hasattr(settings, "EMAIL_SENDER")
        assert hasattr(settings, "GEMINI_API_KEY")
        assert hasattr(settings, "GEMINI_MODEL")
