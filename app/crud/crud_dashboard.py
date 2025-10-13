# mot_back/app/crud/crud_dashboard.py

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
from datetime import date, timedelta

from app.models.answer import Answer
from app.models.question import Question
from app.models.section import Section
from app.models.daily_check_in import DailyCheckIn # <-- Importar DailyCheckIn

def get_questionnaire_summary(db: Session, *, user_id: int) -> List[Dict[str, any]]:
    # ... (esta función se mantiene igual)
    summary_data = (
        db.query(
            Section.name,
            func.avg(Answer.value).label("average_score")
        )
        .join(Question, Section.id == Question.section_id)
        .join(Answer, Question.id == Answer.question_id)
        .filter(Answer.user_id == user_id)
        .group_by(Section.name)
        .all()
    )
    return [
        {"section_name": name, "average_score": score} 
        for name, score in summary_data
    ]

# --- NUEVA FUNCIÓN AÑADIDA ---
def get_user_streak(db: Session, *, user_id: int) -> int:
    """
    Calcula la racha de check-ins consecutivos para un usuario.
    """
    check_ins = (
        db.query(DailyCheckIn.date)
        .filter(DailyCheckIn.user_id == user_id)
        .order_by(DailyCheckIn.date.desc())
        .all()
    )

    if not check_ins:
        return 0

    streak = 0
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # Extraemos solo las fechas de la tupla
    check_in_dates = {c[0] for c in check_ins}

    # Si el último check-in no fue hoy ni ayer, la racha es 0
    if today not in check_in_dates and yesterday not in check_in_dates:
        return 0

    # Si el último check-in fue hoy, la racha es al menos 1
    if today in check_in_dates:
        streak = 1
        current_date = yesterday
    else: # Si el último fue ayer
        streak = 1
        current_date = yesterday - timedelta(days=1)

    # Contamos hacia atrás
    while current_date in check_in_dates:
        streak += 1
        current_date -= timedelta(days=1)

    return streak