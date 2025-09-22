from sqlalchemy import Column, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class DailyCheckIn(Base):
    __tablename__ = "daily_check_ins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    motivation_level = Column(Integer, nullable=False) # Ej: Un valor de 1 a 10

    user = relationship("User")
