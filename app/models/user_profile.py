from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from typing import Optional

from app.db.base import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    
    name: str = Column(String, index=True)
    age: Optional[int] = Column(Integer, nullable=True)
    institution: Optional[str] = Column(String, nullable=True)
    major: Optional[str] = Column(String, nullable=True)
    
    # --- CAMPOS MODIFICADOS ---
    on_medication: Optional[str] = Column(String, nullable=True)
    has_learning_difficulties: Optional[str] = Column(String, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    owner = relationship("User", back_populates="profile")