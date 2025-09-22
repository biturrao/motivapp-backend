from sqlalchemy.orm import declarative_base

# Creamos una clase Base que servirá como la base para todos nuestros modelos ORM.
# SQLAlchemy usará esta base para mapear nuestras clases a las tablas de la base de datos.
Base = declarative_base()
