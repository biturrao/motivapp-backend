from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict

from app.models.answer import Answer
from app.models.question import Question
from app.models.section import Section

def get_questionnaire_summary(db: Session, *, user_id: int) -> List[Dict[str, any]]:
    """
    Calcula el promedio de las respuestas del usuario para cada sección.
    """
    # Esta consulta une Answers, Questions y Sections para agrupar por nombre de sección
    # y calcular el promedio de 'value' para el usuario actual.
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
    
    # Convierte el resultado a un formato de diccionario
    return [
        {"section_name": name, "average_score": score} 
        for name, score in summary_data
    ]
