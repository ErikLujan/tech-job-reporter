from pydantic_settings import BaseSettings, SettingsConfigDict

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
    RESEND_API_KEY: str
    EMAIL_SENDER: str
    EMAIL_RECIPIENT: str

    # API key de Gemini
    GEMINI_API_KEY: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()