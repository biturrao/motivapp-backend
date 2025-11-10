from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class MetamotivationEnergy(Base):
    """
    Modelo para registrar el nivel de energía metamotivacional del usuario
    basado en su selección del semáforo (verde, ámbar, rojo)
    """
    __tablename__ = "metamotivation_energy"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Estado seleccionado en el semáforo
    energy_state = Column(String(20), nullable=False)  # "verde", "ambar", "rojo"
    
    # Timestamp del registro
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relación con el usuario
    user = relationship("User", backref="energy_records")
    
    # Índice compuesto para consultas rápidas por usuario y fecha
    __table_args__ = (
        Index('ix_energy_user_date', 'user_id', 'created_at'),
    )
