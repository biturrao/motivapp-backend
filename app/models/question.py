from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    section_id = Column(Integer, ForeignKey("sections.id"))

    # Relación: Una pregunta pertenece a una sección
    section = relationship("Section", back_populates="questions")
    # Relación: Una pregunta tiene muchas respuestas (usando string)
    answers = relationship("Answer", back_populates="question")

