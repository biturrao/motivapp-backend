from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Creamos el motor de SQLAlchemy usando la URL de la base de datos desde nuestra configuración
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Creamos una clase SessionLocal, cada instancia de esta clase será una sesión de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
