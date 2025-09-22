import random
from typing import List
from sqlalchemy.orm import Session, joinedload

from app.models.question import Question

def get_all_questions_randomized(db: Session) -> List[Question]:
    """
    Obtiene todas las preguntas de la base de datos y las devuelve en orden aleatorio.
    """
    # Usamos joinedload para cargar la sección relacionada en la misma consulta
    # y evitar el problema N+1.
    all_questions = db.query(Question).options(joinedload(Question.section)).all()
    random.shuffle(all_questions)
    return all_questions
