from sqlalchemy.orm import Session
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate

def create_feedback(db: Session, feedback: FeedbackCreate, user_id: int):
    db_feedback = Feedback(
        user_id=user_id,
        message=feedback.message,
        type=feedback.type
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback
