from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Base de datos Azure PostgreSQL
    # Para Azure, construimos la URL desde las variables individuales o usamos la URL completa
    DB_HOST: Optional[str] = None
    DB_NAME: Optional[str] = None
    DB_USER: Optional[str] = None
    DB_PASS: Optional[str] = None
    DATABASE_URL: Optional[str] = None
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Psychologist Invite
    PSYCHOLOGIST_INVITE_KEY: str
    
    # Google Gemini API
    GEMINI_API_KEY: str
    
    # Azure específico
    SCM_DO_BUILD_DURING_DEPLOYMENT: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def get_database_url(self) -> str:
        """
        Construye la DATABASE_URL desde las variables individuales si no está presente,
        útil para Azure que puede proporcionar variables separadas.
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        if all([self.DB_HOST, self.DB_NAME, self.DB_USER, self.DB_PASS]):
            return f"postgresql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}/{self.DB_NAME}?sslmode=require"
        
        raise ValueError("No se pudo construir DATABASE_URL. Proporciona DATABASE_URL o DB_HOST, DB_NAME, DB_USER, DB_PASS")

# Creamos una instancia única de la configuración
settings = Settings()