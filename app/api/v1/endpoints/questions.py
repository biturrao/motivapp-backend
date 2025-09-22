from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import crud_question, crud_answer
from app.models.user import User
from app.schemas.question import QuestionRead
from app.schemas.answer import AnswersRequest # Importar el nuevo schema

router = APIRouter()

@router.get("/", response_model=List[QuestionRead])
def read_questions(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    # ... (código existente del GET) ...
    questions = crud_question.get_all_questions_randomized(db)
    response_data = []
    for q in questions:
        response_data.append({
            "id": q.id,
            "text": q.text,
            "section_name": q.section.name
        })
    return response_data

# --- NUEVO ENDPOINT ---
@router.post("/answers", status_code=status.HTTP_201_CREATED)
def submit_answers(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user), # Seguridad
    answers_in: AnswersRequest
):
    """
    Guarda las respuestas del cuestionario para el usuario autenticado.
    """
    crud_answer.save_user_answers(
        db=db, user_id=current_user.id, answers_in=answers_in.answers
    )
    return {"message": "Respuestas guardadas exitosamente"}