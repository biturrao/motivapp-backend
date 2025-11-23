from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.crud import crud_feedback
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=FeedbackResponse)
def submit_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enviar feedback, reporte de error o sugerencia.
    """
    return crud_feedback.create_feedback(db=db, feedback=feedback, user_id=current_user.id)
