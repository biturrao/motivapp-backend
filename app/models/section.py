from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.db.base import Base

class Section(Base):
    """Model for learning path sections (e.g., Iniciar, Autoregulación, etc.)"""
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False)
    description = Column(Text)
    order = Column(Integer, nullable=False, default=0)  # Order in the path (1, 2, 3, 4)
    icon_name = Column(String(50))  # Icon identifier for frontend
    
    # Relationships
    questions = relationship("Question", back_populates="section")
    contents = relationship("Content", back_populates="section", cascade="all, delete-orphan")
    lessons = relationship("Lesson", back_populates="section", cascade="all, delete-orphan")
