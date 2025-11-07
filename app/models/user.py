from sqlalchemy import Column, Integer, String, Boolean, Index
from sqlalchemy.orm import relationship

from app.db.base import Base
from .user_profile import UserProfile 

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean(), default=True)

    # --- CAMBIO: Añadimos el campo de rol ---
    # Por defecto, cualquier usuario nuevo será un "student"
    # Los psicólogos tendrán el rol "psychologist"
    role = Column(String, default="student", nullable=False)

    # Relación inversa con las respuestas
    answers = relationship("Answer", back_populates="user")
    
    # Conecta este usuario con su perfil
    profile = relationship("UserProfile", back_populates="owner", uselist=False)
    
    # Path progress relationships
    content_progress = relationship("UserContentProgress", back_populates="user", cascade="all, delete-orphan")
    lesson_progress = relationship("UserLessonProgress", back_populates="user", cascade="all, delete-orphan")
    section_progress = relationship("UserSectionProgress", back_populates="user", cascade="all, delete-orphan")

