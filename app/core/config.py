from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Base de datos
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_NAME: str
    DATABASE_HOST: str
    DATABASE_PORT: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    @property
    def DATABASE_URL(self) -> str:
        """
        Genera la URL de conexión a la base de datos a partir de las variables de entorno.
        """
        return (f"postgresql+psycopg2://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@"
                f"{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}")

# Creamos una instancia única de la configuración que se importará en otros módulos
settings = Settings()
