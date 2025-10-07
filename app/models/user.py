# mot_back/app/models/user.py

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.db.base import Base
# Importamos el nuevo modelo para poder referenciarlo
from .user_profile import UserProfile 

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean(), default=True)

    # Relación inversa con las respuestas
    answers = relationship("Answer", back_populates="user")
    
    # --- LÍNEA AÑADIDA ---
    # Conecta este usuario con su perfil
    profile = relationship("UserProfile", back_populates="owner", uselist=False)