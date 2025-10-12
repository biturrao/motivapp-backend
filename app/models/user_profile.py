# mot_back/app/models/user_profile.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from typing import Optional

from app.db.base import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    
    # Bloque 1
    name: str = Column(String, index=True)
    age: Optional[int] = Column(Integer, nullable=True)
    major: Optional[str] = Column(String, nullable=True)
    entry_year: Optional[int] = Column(Integer, nullable=True) # Año de ingreso
    course_types: Optional[str] = Column(String, nullable=True) # Tipo de asignaturas

    # Bloque 2
    family_responsibilities: Optional[str] = Column(String, nullable=True) # Sí / No / Prefiero...
    is_working: Optional[str] = Column(String, nullable=True) # Sí / No / Parcial

    # Bloque 3
    mental_health_support: Optional[str] = Column(String, nullable=True) # Sí / No / Prefiero...
    mental_health_details: Optional[str] = Column(String, nullable=True) # Detalle opcional
    chronic_condition: Optional[str] = Column(String, nullable=True) # Sí / No / Prefiero...
    chronic_condition_details: Optional[str] = Column(String, nullable=True) # Detalle opcional

    # Bloque 4
    neurodivergence: Optional[str] = Column(String, nullable=True) # Sí / No / Prefiero...
    neurodivergence_details: Optional[str] = Column(String, nullable=True) # Detalle opcional
    preferred_support_types: Optional[str] = Column(String, nullable=True) # Chips

    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    owner = relationship("User", back_populates="profile")