from pydantic import BaseModel
from typing import Optional, List
from app.schemas.content import ContentWithProgress
from app.schemas.lesson import LessonWithProgress


class SectionBase(BaseModel):
    name: str
    description: Optional[str] = None
    order: int
    icon_name: Optional[str] = None


class SectionCreate(SectionBase):
    pass


class SectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    icon_name: Optional[str] = None


class Section(SectionBase):
    id: int

    class Config:
        from_attributes = True


class SectionWithProgress(Section):
    contents: List[ContentWithProgress] = []
    lessons: List[LessonWithProgress] = []
    completed_contents: int = 0
    total_contents: int = 0
    completed_lessons: int = 0
    total_lessons: int = 0
    current_content_order: int = 1
    current_lesson_order: int = 1
    is_completed: bool = False
