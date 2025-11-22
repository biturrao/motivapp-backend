from pydantic import BaseModel
from datetime import date

class DailyCheckInCreate(BaseModel):
    motivation_level: int

class DailyCheckInRead(BaseModel):
    date: date
    motivation_level: int
    message: str | None = None
    action: str | None = None

    class Config:
        from_attributes = True


# Alias para compatibilidad
DailyCheckIn = DailyCheckInRead
