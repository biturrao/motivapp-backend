from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.models.user_progress import (
    UserContentProgress, 
    UserLessonProgress, 
    UserSectionProgress
)
from app.models.section import Section
from app.models.content import Content
from app.models.lesson import Lesson
from app.schemas.user_progress import (
    UserContentProgressCreate,
    UserLessonProgressCreate,
    UserSectionProgressCreate,
    PathOverview
)


# Content Progress
def get_user_content_progress(
    db: Session, user_id: int, content_id: int
) -> Optional[UserContentProgress]:
    """Get user progress for a specific content"""
    return db.query(UserContentProgress).filter(
        UserContentProgress.user_id == user_id,
        UserContentProgress.content_id == content_id
    ).first()


def get_all_user_content_progress(db: Session, user_id: int) -> List[UserContentProgress]:
    """Get all content progress for a user"""
    return db.query(UserContentProgress).filter(
        UserContentProgress.user_id == user_id
    ).all()


def create_or_update_content_progress(
    db: Session, user_id: int, progress: UserContentProgressCreate
) -> UserContentProgress:
    """Create or update content progress"""
    db_progress = get_user_content_progress(db, user_id, progress.content_id)
    
    if db_progress:
        db_progress.completed = progress.completed
        db_progress.last_accessed = datetime.utcnow()
        if progress.completed and not db_progress.completed_at:
            db_progress.completed_at = datetime.utcnow()
    else:
        db_progress = UserContentProgress(
            user_id=user_id,
            content_id=progress.content_id,
            completed=progress.completed,
            completed_at=datetime.utcnow() if progress.completed else None,
            last_accessed=datetime.utcnow()
        )
        db.add(db_progress)
    
    db.commit()
    db.refresh(db_progress)
    return db_progress


# Lesson Progress
def get_user_lesson_progress(
    db: Session, user_id: int, lesson_id: int
) -> Optional[UserLessonProgress]:
    """Get user progress for a specific lesson"""
    return db.query(UserLessonProgress).filter(
        UserLessonProgress.user_id == user_id,
        UserLessonProgress.lesson_id == lesson_id
    ).first()


def get_all_user_lesson_progress(db: Session, user_id: int) -> List[UserLessonProgress]:
    """Get all lesson progress for a user"""
    return db.query(UserLessonProgress).filter(
        UserLessonProgress.user_id == user_id
    ).all()


def create_or_update_lesson_progress(
    db: Session, user_id: int, progress: UserLessonProgressCreate
) -> UserLessonProgress:
    """Create or update lesson progress"""
    db_progress = get_user_lesson_progress(db, user_id, progress.lesson_id)
    
    if db_progress:
        db_progress.completed = progress.completed
        db_progress.last_accessed = datetime.utcnow()
        if progress.completed and not db_progress.completed_at:
            db_progress.completed_at = datetime.utcnow()
    else:
        db_progress = UserLessonProgress(
            user_id=user_id,
            lesson_id=progress.lesson_id,
            completed=progress.completed,
            completed_at=datetime.utcnow() if progress.completed else None,
            last_accessed=datetime.utcnow()
        )
        db.add(db_progress)
    
    db.commit()
    db.refresh(db_progress)
    return db_progress


# Section Progress
def get_user_section_progress(
    db: Session, user_id: int, section_id: int
) -> Optional[UserSectionProgress]:
    """Get user progress for a specific section"""
    return db.query(UserSectionProgress).filter(
        UserSectionProgress.user_id == user_id,
        UserSectionProgress.section_id == section_id
    ).first()


def get_all_user_section_progress(db: Session, user_id: int) -> List[UserSectionProgress]:
    """Get all section progress for a user"""
    return db.query(UserSectionProgress).filter(
        UserSectionProgress.user_id == user_id
    ).all()


def create_or_update_section_progress(
    db: Session, user_id: int, progress: UserSectionProgressCreate
) -> UserSectionProgress:
    """Create or update section progress"""
    db_progress = get_user_section_progress(db, user_id, progress.section_id)
    
    if db_progress:
        db_progress.current_content_order = progress.current_content_order
        db_progress.current_lesson_order = progress.current_lesson_order
        db_progress.completed = progress.completed
        if progress.completed and not db_progress.completed_at:
            db_progress.completed_at = datetime.utcnow()
    else:
        db_progress = UserSectionProgress(
            user_id=user_id,
            section_id=progress.section_id,
            current_content_order=progress.current_content_order,
            current_lesson_order=progress.current_lesson_order,
            completed=progress.completed,
            completed_at=datetime.utcnow() if progress.completed else None
        )
        db.add(db_progress)
    
    db.commit()
    db.refresh(db_progress)
    return db_progress


def get_path_overview(db: Session, user_id: int) -> PathOverview:
    """Get overall path progress overview for a user"""
    # Get all sections
    all_sections = db.query(Section).order_by(Section.order).all()
    total_sections = len(all_sections)
    
    # Get completed sections
    completed_sections = db.query(UserSectionProgress).filter(
        UserSectionProgress.user_id == user_id,
        UserSectionProgress.completed == True
    ).count()
    
    # Find current section (first incomplete section)
    current_section = None
    for section in all_sections:
        section_progress = get_user_section_progress(db, user_id, section.id)
        if not section_progress or not section_progress.completed:
            current_section = section
            break
    
    # Calculate overall progress percentage
    progress_percentage = (completed_sections / total_sections * 100) if total_sections > 0 else 0
    
    return PathOverview(
        total_sections=total_sections,
        completed_sections=completed_sections,
        current_section_id=current_section.id if current_section else None,
        current_section_name=current_section.name if current_section else None,
        overall_progress_percentage=round(progress_percentage, 2)
    )


def initialize_user_section_progress(db: Session, user_id: int) -> None:
    """Initialize section progress for a new user (create entries for all sections)"""
    sections = db.query(Section).all()
    
    for section in sections:
        existing = get_user_section_progress(db, user_id, section.id)
        if not existing:
            db_progress = UserSectionProgress(
                user_id=user_id,
                section_id=section.id,
                current_content_order=1,
                current_lesson_order=1,
                completed=False
            )
            db.add(db_progress)
    
    db.commit()
