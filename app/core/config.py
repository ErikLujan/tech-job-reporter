from pydantic_settings import BaseSettings, SettingsConfigDict

# Constantes del pipeline ETL — centralizadas para evitar números/strings mágicos
DREAM_JOBS_LIMIT = 5
TOP_TECHNOLOGIES_LIMIT = 10
CHART_COLOR = "#2563eb"
CHART_STYLE = "default"  # estilo integrado de matplotlib (seaborn no está en deps)
FIGURE_SIZE = (10, 6)


class Settings(BaseSettings):
    """
    Configuración centralizada del proyecto Tech Job Reporter.

    Pydantic se encarga automáticamente de leer el archivo .env,
    validar que las variables requeridas existan y tengan el tipo de dato correcto.
    Si falta alguna clave crítica, el script lanzará un error detallado y se detendrá
    antes de ejecutar cualquier lógica.
    """

    # Credenciales de Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # Credenciales de Resend
    # IMPORTANTE: EMAIL_SENDER debe ser un dominio verificado en Resend (ej. reportes@tudominio.com)
    # o el correo rebotará. onboarding@resend.dev funciona solo para pruebas en cuentas propias.
    RESEND_API_KEY: str
    EMAIL_SENDER: str

    # API key de Gemini
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignora campos extra en .env (ej. EMAIL_RECIPIENT, GITHUB_PAT)
    )


settings = Settings()  # type: ignore[call-arg]  # Pydantic lee del env_file, mypy no lo entiende
