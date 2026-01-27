"""
Configuración de la aplicación - Lee variables de entorno desde .env
"""

from pydantic_settings import BaseSettings
from typing import Optional


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
    SECRET_KEY: str = "tu-clave-super-secreta-cambiala-en-produccion"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Sportmonks API
    SPORTMONKS_API_KEY: str = ""
    SPORTMONKS_BASE_URL: str = "https://api.sportmonks.com/v3"
    
    # Frontend URL (para CORS)
    FRONTEND_URL: str = "http://localhost:5173"
    
    # Entorno
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    @property
    def database_url(self) -> str:
        """
        Construye la URL de conexión a MySQL
        Formato: mysql+pymysql://user:password@host:port/database
        """
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instancia global de configuración
settings = Settings()
