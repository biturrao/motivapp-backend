# mot_back/app/crud/crud_answer.py

from sqlalchemy.orm import Session
from typing import List

from app.models.answer import Answer
from app.schemas.answer import AnswerCreate

def save_user_answers(db: Session, *, user_id: int, answers_in: List[AnswerCreate]):
    """
    Guarda o actualiza un lote de respuestas para un usuario específico.
    Borra las respuestas antiguas del usuario y luego inserta las nuevas.
    """
    # Borra las respuestas antiguas para este usuario
    db.query(Answer).filter(Answer.user_id == user_id).delete(synchronize_session=False)

    # Crea y añade las nuevas respuestas
    db_answers = [
        Answer(user_id=user_id, question_id=ans.question_id, value=ans.value)
        for ans in answers_in
    ]
    
    db.add_all(db_answers)
    db.commit()