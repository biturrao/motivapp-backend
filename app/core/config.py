from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Base de datos
    # Ahora esperamos la URL completa directamente del entorno
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

# Creamos una instancia única de la configuración
settings = Settings()