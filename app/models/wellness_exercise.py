from sqlalchemy import Column, Integer, String, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class ExerciseState(str, enum.Enum):
    """Estado recomendado del semáforo para el ejercicio"""
    VERDE = "verde"
    AMBAR = "ambar"
    ROJO = "rojo"
    CUALQUIERA = "cualquiera"


class WellnessExercise(Base):
    """
    Modelo para almacenar los ejercicios de bienestar (embodied cognition + mindfulness)
    """
    __tablename__ = "wellness_exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    objective = Column(String(500), nullable=False)
    context = Column(String(200), nullable=False)  # Sentado, De pie, etc.
    duration_seconds = Column(Integer, nullable=False)  # Duración en segundos
    recommended_state = Column(SQLEnum(ExerciseState), nullable=False)
    
    # Taxonomía y detalles del ejercicio
    taxonomy = Column(Text, nullable=False)  # Qué trabaja el ejercicio
    body_systems = Column(Text, nullable=False)  # Sistemas corporales implicados
    
    # Pasos del ejercicio (almacenado como JSON text)
    steps = Column(Text, nullable=False)
    
    # Guiones de voz (almacenado como JSON text)
    voice_scripts = Column(Text, nullable=False)
    
    # Medición pre/post
    measurement_notes = Column(Text, nullable=True)
    
    # Notas de UX/UI
    ux_notes = Column(Text, nullable=True)
    
    # Salvaguardas
    safeguards = Column(Text, nullable=True)
    
    # Relación con completaciones
    completions = relationship("ExerciseCompletion", back_populates="exercise", cascade="all, delete-orphan")
