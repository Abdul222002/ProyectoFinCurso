"""
Configuración de la aplicación - Lee variables de entorno desde .env
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """
    Configuración principal de la aplicación
    Pydantic automáticamente lee del archivo .env
    """
    
    # Base de Datos MySQL
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str = "ultimate_fantasy_legends"
    
    # JWT para autenticación
    # Sin valor por defecto: fuerza configuración explícita vía .env o variable de entorno
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 días
    
    # Sportmonks API
    # Sin valor por defecto: fuerza configuración explícita vía .env o variable de entorno  
    SPORTMONKS_API_KEY: str
    SPORTMONKS_BASE_URL: str = "https://api.sportmonks.com/v3"
    
    # Frontend URL (para CORS)
    FRONTEND_URL: str = "http://localhost:5173"
    
    # Entorno
    ENVIRONMENT: str = "production"
    DEBUG: bool = False

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_strong(cls, v: str) -> str:
        if not v or len(v) < 32:
            raise ValueError(
                "SECRET_KEY debe tener al menos 32 caracteres. "
                "Genérala con: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        bad_keys = (
            "tu-clave-super-secreta-cambiala-en-produccion",
            "changeme",
            "secret",
            "supersecret",
        )
        if v in bad_keys:
            raise ValueError("SECRET_KEY es la clave de ejemplo. Cámbiala en tu .env")
        return v
    
    @property
    def database_url(self) -> str:
        """
        Construye la URL de conexión a MySQL
        Formato: mysql+pymysql://user:password@host:port/database
        """
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            "?charset=utf8mb4"
        )
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


# Instancia global de configuración
settings = Settings()
