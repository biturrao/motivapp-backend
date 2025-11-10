from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class ExerciseCompletion(Base):
    """
    Modelo para registrar las completaciones de ejercicios de bienestar
    Evita que el mismo ejercicio se repita para el mismo usuario en el mismo día
    """
    __tablename__ = "exercise_completions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_id = Column(Integer, ForeignKey("wellness_exercises.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Estado del semáforo cuando se realizó
    energy_state = Column(String(20), nullable=False)  # "verde", "ambar", "rojo"
    
    # Mediciones pre/post
    intensity_pre = Column(Integer, nullable=True)  # 0-10
    intensity_post = Column(Integer, nullable=True)  # 0-10
    
    # Notas del usuario sobre el ejercicio
    user_notes = Column(Text, nullable=True)
    
    # Si el ejercicio fue completado exitosamente
    completed = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relaciones
    user = relationship("User", backref="exercise_completions")
    exercise = relationship("WellnessExercise", back_populates="completions")
    
    # Índices para optimizar consultas
    __table_args__ = (
        Index('ix_completion_user_exercise', 'user_id', 'exercise_id'),
        Index('ix_completion_user_date', 'user_id', 'started_at'),
    )
