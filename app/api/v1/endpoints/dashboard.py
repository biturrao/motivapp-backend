from typing import List
from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.daily_check_in import DailyCheckIn
from app.schemas.daily_check_in import DailyCheckInRead
from app.crud import crud_dashboard
from app.schemas.dashboard import SectionAverage
from app.crud import crud_daily_check_in, crud_answer
from app.schemas.answer import AnswerRead

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


@router.get("/path-streak", response_model=dict)
def get_path_streak_endpoint(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Obtiene la racha de días consecutivos usando el path (contenidos o lecciones).
    """
    streak = crud_dashboard.get_path_streak(db=db, user_id=current_user.id)
    return {"streak": streak}


@router.get("/admin/user/{user_id}/motivation-history", response_model=List[DailyCheckInRead])
def get_user_motivation_history(
    *,
    db: Session = Depends(deps.get_db),
    # Protección: Solo psicólogos pueden acceder
    current_psychologist: User = Depends(deps.get_current_psychologist_user),
    user_id: int  # El ID del estudiante que se está consultando
):
    """
    (Admin) Obtiene el historial de motivación para un usuario específico.
    """
    # Aquí podríamos añadir lógica para verificar que user_id sea un 'student'
    # pero por ahora, la función CRUD es suficiente.
    history = crud_daily_check_in.get_check_ins_by_user_id(db=db, user_id=user_id)
    return history

@router.get("/admin/user/{user_id}/questionnaire-summary", response_model=List[SectionAverage])
def get_user_questionnaire_summary(
    *,
    db: Session = Depends(deps.get_db),
    # Protección: Solo psicólogos pueden acceder
    current_psychologist: User = Depends(deps.get_current_psychologist_user),
    user_id: int
):
    """
    (Admin) Obtiene el resumen del cuestionario (para gráfica de radar)
    de un usuario específico.
    """
    summary = crud_dashboard.get_questionnaire_summary(db=db, user_id=user_id)
    return summary

@router.get("/admin/user/{user_id}/answers", response_model=List[AnswerRead])
def get_user_answers(
    *,
    db: Session = Depends(deps.get_db),
    # Protección: Solo psicólogos pueden acceder
    current_psychologist: User = Depends(deps.get_current_psychologist_user),
    user_id: int
):
    """
    (Admin) Obtiene todas las respuestas del cuestionario de un usuario específico.
    """
    answers = crud_answer.get_answers_by_user_id(db=db, user_id=user_id)
    return answers