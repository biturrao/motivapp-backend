from typing import List
from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.daily_check_in import DailyCheckIn
from app.schemas.daily_check_in import DailyCheckInRead
# Nuevos imports
from app.crud import crud_dashboard
from app.schemas.dashboard import SectionAverage

router = APIRouter()

@router.get("/motivation-history", response_model=List[DailyCheckInRead])
def get_motivation_history(
    # ... (código del endpoint existente)
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    start_date = date.today() - timedelta(days=6)
    results = (
        db.query(DailyCheckIn)
        .filter(DailyCheckIn.user_id == current_user.id, DailyCheckIn.date >= start_date)
        .order_by(DailyCheckIn.date.asc())
        .all()
    )
    return results

# --- NUEVO ENDPOINT PARA GRÁFICA DE RADAR ---
@router.get("/questionnaire-summary", response_model=List[SectionAverage])
def get_questionnaire_summary_data(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Obtiene el puntaje promedio por sección para el usuario autenticado.
    Estos son los datos para la gráfica de radar.
    """
    summary = crud_dashboard.get_questionnaire_summary(db=db, user_id=current_user.id)
    return summary

    return results

@router.get("/streak", response_model=dict)
def get_user_streak_endpoint(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Obtiene la racha de check-ins consecutivos del usuario actual.
    """
    streak = crud_dashboard.get_user_streak(db=db, user_id=current_user.id)
    return {"streak": streak}