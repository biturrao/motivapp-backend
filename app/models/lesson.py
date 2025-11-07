from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class Lesson(Base):
    """Model for lessons within sections"""
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    content_url = Column(String(500))  # URL for lesson content
    duration_minutes = Column(Integer)
    order = Column(Integer, nullable=False)  # Order within the section
    
    # Relationships
    section = relationship("Section", back_populates="lessons")
    user_progress = relationship("UserLessonProgress", back_populates="lesson", cascade="all, delete-orphan")
