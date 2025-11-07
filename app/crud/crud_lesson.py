from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.lesson import Lesson
from app.schemas.lesson import LessonCreate, LessonUpdate


def get_lesson(db: Session, lesson_id: int) -> Optional[Lesson]:
    """Get a single lesson by ID"""
    return db.query(Lesson).filter(Lesson.id == lesson_id).first()


def get_lessons_by_section(db: Session, section_id: int) -> List[Lesson]:
    """Get all lessons for a specific section, ordered by order field"""
    return db.query(Lesson).filter(
        Lesson.section_id == section_id
    ).order_by(Lesson.order).all()


def create_lesson(db: Session, lesson: LessonCreate) -> Lesson:
    """Create a new lesson"""
    db_lesson = Lesson(**lesson.dict())
    db.add(db_lesson)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson


def update_lesson(db: Session, lesson_id: int, lesson: LessonUpdate) -> Optional[Lesson]:
    """Update a lesson"""
    db_lesson = get_lesson(db, lesson_id)
    if db_lesson:
        update_data = lesson.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_lesson, field, value)
        db.commit()
        db.refresh(db_lesson)
    return db_lesson


def delete_lesson(db: Session, lesson_id: int) -> bool:
    """Delete a lesson"""
    db_lesson = get_lesson(db, lesson_id)
    if db_lesson:
        db.delete(db_lesson)
        db.commit()
        return True
    return False
