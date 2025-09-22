from sqlalchemy.orm import Session
from typing import List

from app.models.answer import Answer
from app.schemas.answer import AnswerCreate

def save_user_answers(db: Session, *, user_id: int, answers_in: List[AnswerCreate]):
    """
    Guarda o actualiza un lote de respuestas para un usuario específico.
    """
    # Una estrategia común es borrar las respuestas antiguas del usuario para
    # el cuestionario y luego insertar las nuevas.
    # Esto simplifica la lógica para "volver a tomar" el test.
    db.query(Answer).filter(Answer.user_id == user_id).delete(synchronize_session=False)

    # Crear y añadir las nuevas respuestas
    db_answers = [
        Answer(user_id=user_id, question_id=ans.question_id, value=ans.value)
        for ans in answers_in
    ]
    
    db.add_all(db_answers)
    db.commit()
