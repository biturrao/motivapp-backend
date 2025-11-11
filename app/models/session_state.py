# app/models/session_state.py

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class SessionState(Base):
    """
    Modelo para persistir el estado de la sesión metamotivacional de cada usuario.
    Guarda el progreso del ciclo de tutoreo de Flou.
    """
    __tablename__ = "session_states"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Estado de sesión
    greeted = Column(Boolean, default=False, nullable=False)
    iteration = Column(Integer, default=0, nullable=False)
    
    # Sentimientos
    sentimiento_inicial = Column(String, nullable=True)
    sentimiento_actual = Column(String, nullable=True)
    
    # Slots extraídos (guardados como JSON)
    slots = Column(JSON, nullable=True, default={})
    
    # Clasificaciones Q2, Q3
    Q2 = Column(String, nullable=True)  # "A" o "B"
    Q3 = Column(String, nullable=True)  # "↑", "↓" o "mixto"
    enfoque = Column(String, nullable=True)  # "promocion_eager" o "prevencion_vigilant"
    
    # Configuración de bloque
    tiempo_bloque = Column(Integer, nullable=True)  # 10, 12, 15, 25
    
    # Estrategia y evaluación
    last_strategy = Column(Text, nullable=True)
    last_eval_result = Column(JSON, nullable=True, default={})  # {exito: bool, cambio_sentimiento: "↑"|"="|"↓"}
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relación con el usuario
    user = relationship("User", back_populates="session_state")
