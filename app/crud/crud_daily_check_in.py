from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import List
from app.models.daily_check_in import DailyCheckIn
from app.schemas.daily_check_in import DailyCheckInCreate

def save_check_in(db: Session, *, user_id: int, check_in_in: DailyCheckInCreate) -> DailyCheckIn:
    # Busca si ya existe un check-in para este usuario en este día
    db_check_in = db.query(DailyCheckIn).filter(
        DailyCheckIn.user_id == user_id, 
        DailyCheckIn.date == date.today()
    ).first()

    if db_check_in:
        # Si existe, lo actualiza
        db_check_in.motivation_level = check_in_in.motivation_level
    else:
        # Si no existe, lo crea
        db_check_in = DailyCheckIn(
            user_id=user_id,
            date=date.today(),
            motivation_level=check_in_in.motivation_level
        )
        db.add(db_check_in)
    
    db.commit()
    db.refresh(db_check_in)
    return db_check_in

def get_check_ins_by_user_id(db: Session, *, user_id: int) -> List[DailyCheckIn]:
    """
    Obtiene el historial de check-ins de motivación para un usuario específico.
    Por defecto, obtiene los últimos 30 días.
    """
    start_date = date.today() - timedelta(days=29) # Historial de 30 días
    return (
        db.query(DailyCheckIn)
        .filter(DailyCheckIn.user_id == user_id, DailyCheckIn.date >= start_date)
        .order_by(DailyCheckIn.date.asc())
        .all()
    )