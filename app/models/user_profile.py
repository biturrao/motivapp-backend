# mot_back/app/models/user_profile.py

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from typing import Optional

from app.db.base import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    
    # --- Campos del Perfil ---
    name: str = Column(String, index=True)
    age: Optional[int] = Column(Integer, nullable=True)
    institution: Optional[str] = Column(String, nullable=True) # Dónde estudia
    major: Optional[str] = Column(String, nullable=True)      # Qué estudia
    
    # Usamos Booleanos para preguntas de sí/no
    on_medication: Optional[bool] = Column(Boolean(), nullable=True)
    has_learning_difficulties: Optional[bool] = Column(Boolean(), nullable=True)

    # --- Relación con el Usuario ---
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    owner = relationship("User", back_populates="profile")