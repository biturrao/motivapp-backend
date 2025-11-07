from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class ContentType(str, enum.Enum):
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"


class Content(Base):
    """Model for theoretical executable content (videos, audio, text)"""
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    content_type = Column(Enum(ContentType), nullable=False)
    content_url = Column(String(500))  # URL for video/audio or text content
    duration_minutes = Column(Integer)  # Duration for videos/audio
    order = Column(Integer, nullable=False)  # Order within the section
    
    # Relationships
    section = relationship("Section", back_populates="contents")
    user_progress = relationship("UserContentProgress", back_populates="content", cascade="all, delete-orphan")
