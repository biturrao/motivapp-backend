from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base

class Section(Base):
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    
    # Usar string para la clase "Question"
    questions = relationship("Question", back_populates="section")
