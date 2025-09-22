from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship # <-- Asegúrate de importar relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean(), default=True)

    # Añadir esta relación inversa
    answers = relationship("Answer", back_populates="user")