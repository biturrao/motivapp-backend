from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Obtenemos la URL de la base de datos (puede ser construida o directa)
database_url = settings.get_database_url()

# Configuración específica para Azure PostgreSQL
# - pool_pre_ping: Verifica conexiones antes de usarlas (importante para conexiones que pueden cerrarse)
# - connect_args: Configuraciones SSL y timeouts para Azure
# - pool_size: Tamaño del pool de conexiones
# - max_overflow: Conexiones adicionales permitidas
# - pool_recycle: Recicla conexiones después de 3600 segundos (1 hora)

connect_args = {
    "sslmode": "require",  # Azure PostgreSQL requiere SSL
    "connect_timeout": 10,  # Timeout de conexión en segundos
}

# Creamos el motor de SQLAlchemy usando la URL de la base de datos desde nuestra configuración
engine = create_engine(
    database_url, 
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,
    connect_args=connect_args
)

# Creamos una clase SessionLocal, cada instancia de esta clase será una sesión de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
