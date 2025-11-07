from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.section import Section, SectionWithProgress
from app.schemas.content import ContentWithProgress
from app.schemas.lesson import LessonWithProgress
from app.schemas.user_progress import (
    UserContentProgressCreate,
    UserLessonProgressCreate,
    UserSectionProgressCreate,
    PathOverview
)
from app.crud import crud_section, crud_content, crud_lesson, crud_path

router = APIRouter()


@router.get("/overview", response_model=PathOverview)
def get_path_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get overview of user's entire path progress"""
    # Initialize section progress if not exists
    crud_path.initialize_user_section_progress(db, current_user.id)
    return crud_path.get_path_overview(db, current_user.id)


@router.get("/sections", response_model=List[SectionWithProgress])
def get_all_sections_with_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all sections with user's progress"""
    # Initialize section progress if not exists
    crud_path.initialize_user_section_progress(db, current_user.id)
    
    sections = crud_section.get_all_sections(db)
    result = []
    
    for section in sections:
        # Get section progress
        section_progress = crud_path.get_user_section_progress(
            db, current_user.id, section.id
        )
        
        # Get contents with progress
        contents = crud_content.get_contents_by_section(db, section.id)
        content_progress_list = []
        completed_contents = 0
        
        for content in contents:
            progress = crud_path.get_user_content_progress(
                db, current_user.id, content.id
            )
            content_with_progress = ContentWithProgress(
                id=content.id,
                section_id=content.section_id,
                title=content.title,
                description=content.description,
                content_type=content.content_type,
                content_url=content.content_url,
                duration_minutes=content.duration_minutes,
                order=content.order,
                completed=progress.completed if progress else False,
                last_accessed=progress.last_accessed.isoformat() if progress else None
            )
            content_progress_list.append(content_with_progress)
            if progress and progress.completed:
                completed_contents += 1
        
        # Get lessons with progress
        lessons = crud_lesson.get_lessons_by_section(db, section.id)
        lesson_progress_list = []
        completed_lessons = 0
        
        for lesson in lessons:
            progress = crud_path.get_user_lesson_progress(
                db, current_user.id, lesson.id
            )
            lesson_with_progress = LessonWithProgress(
                id=lesson.id,
                section_id=lesson.section_id,
                title=lesson.title,
                description=lesson.description,
                content_url=lesson.content_url,
                duration_minutes=lesson.duration_minutes,
                order=lesson.order,
                completed=progress.completed if progress else False,
                last_accessed=progress.last_accessed.isoformat() if progress else None
            )
            lesson_progress_list.append(lesson_with_progress)
            if progress and progress.completed:
                completed_lessons += 1
        
        # Build section with progress
        section_with_progress = SectionWithProgress(
            id=section.id,
            name=section.name,
            description=section.description,
            order=section.order,
            icon_name=section.icon_name,
            contents=content_progress_list,
            lessons=lesson_progress_list,
            completed_contents=completed_contents,
            total_contents=len(contents),
            completed_lessons=completed_lessons,
            total_lessons=len(lessons),
            current_content_order=section_progress.current_content_order if section_progress else 1,
            current_lesson_order=section_progress.current_lesson_order if section_progress else 1,
            is_completed=section_progress.completed if section_progress else False
        )
        result.append(section_with_progress)
    
    return result


@router.get("/sections/{section_id}", response_model=SectionWithProgress)
def get_section_with_progress(
    section_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific section with user's progress"""
    section = crud_section.get_section(db, section_id)
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    # Get section progress
    section_progress = crud_path.get_user_section_progress(
        db, current_user.id, section.id
    )
    
    # Get contents with progress
    contents = crud_content.get_contents_by_section(db, section.id)
    content_progress_list = []
    completed_contents = 0
    
    for content in contents:
        progress = crud_path.get_user_content_progress(
            db, current_user.id, content.id
        )
        content_with_progress = ContentWithProgress(
            id=content.id,
            section_id=content.section_id,
            title=content.title,
            description=content.description,
            content_type=content.content_type,
            content_url=content.content_url,
            duration_minutes=content.duration_minutes,
            order=content.order,
            completed=progress.completed if progress else False,
            last_accessed=progress.last_accessed.isoformat() if progress else None
        )
        content_progress_list.append(content_with_progress)
        if progress and progress.completed:
            completed_contents += 1
    
    # Get lessons with progress
    lessons = crud_lesson.get_lessons_by_section(db, section.id)
    lesson_progress_list = []
    completed_lessons = 0
    
    for lesson in lessons:
        progress = crud_path.get_user_lesson_progress(
            db, current_user.id, lesson.id
        )
        lesson_with_progress = LessonWithProgress(
            id=lesson.id,
            section_id=lesson.section_id,
            title=lesson.title,
            description=lesson.description,
            content_url=lesson.content_url,
            duration_minutes=lesson.duration_minutes,
            order=lesson.order,
            completed=progress.completed if progress else False,
            last_accessed=progress.last_accessed.isoformat() if progress else None
        )
        lesson_progress_list.append(lesson_with_progress)
        if progress and progress.completed:
            completed_lessons += 1
    
    return SectionWithProgress(
        id=section.id,
        name=section.name,
        description=section.description,
        order=section.order,
        icon_name=section.icon_name,
        contents=content_progress_list,
        lessons=lesson_progress_list,
        completed_contents=completed_contents,
        total_contents=len(contents),
        completed_lessons=completed_lessons,
        total_lessons=len(lessons),
        current_content_order=section_progress.current_content_order if section_progress else 1,
        current_lesson_order=section_progress.current_lesson_order if section_progress else 1,
        is_completed=section_progress.completed if section_progress else False
    )


@router.post("/content/progress")
def update_content_progress(
    progress: UserContentProgressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update progress for a specific content"""
    # Verify content exists
    content = crud_content.get_content(db, progress.content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    return crud_path.create_or_update_content_progress(db, current_user.id, progress)


@router.post("/lesson/progress")
def update_lesson_progress(
    progress: UserLessonProgressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update progress for a specific lesson"""
    # Verify lesson exists
    lesson = crud_lesson.get_lesson(db, progress.lesson_id)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    return crud_path.create_or_update_lesson_progress(db, current_user.id, progress)


@router.post("/section/progress")
def update_section_progress(
    progress: UserSectionProgressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update progress for a specific section"""
    # Verify section exists
    section = crud_section.get_section(db, progress.section_id)
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    return crud_path.create_or_update_section_progress(db, current_user.id, progress)
