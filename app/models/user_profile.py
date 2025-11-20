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
    institution: Optional[str] = Column(String, nullable=True) # <-- LÍNEA AÑADIDA
    major: Optional[str] = Column(String, nullable=True)
    entry_year: Optional[int] = Column(Integer, nullable=True)
    course_types: Optional[str] = Column(String, nullable=True)

    # Bloque 2
    family_responsibilities: Optional[str] = Column(String, nullable=True)
    is_working: Optional[str] = Column(String, nullable=True)

    # Bloque 3
    mental_health_support: Optional[str] = Column(String, nullable=True)
    mental_health_details: Optional[str] = Column(String, nullable=True)
    chronic_condition: Optional[str] = Column(String, nullable=True)
    chronic_condition_details: Optional[str] = Column(String, nullable=True)

    # Bloque 4
    neurodivergence: Optional[str] = Column(String, nullable=True)
    neurodivergence_details: Optional[str] = Column(String, nullable=True)
    preferred_support_types: Optional[str] = Column(String, nullable=True)
    
    # Cache del resumen generado por IA
    summary: Optional[str] = Column(String, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    owner = relationship("User", back_populates="profile")