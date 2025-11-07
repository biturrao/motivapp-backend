from pydantic import BaseModel
from typing import Optional


class LessonBase(BaseModel):
    title: str
    description: Optional[str] = None
    content_url: Optional[str] = None
    duration_minutes: Optional[int] = None
    order: int


class LessonCreate(LessonBase):
    section_id: int


class LessonUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content_url: Optional[str] = None
    duration_minutes: Optional[int] = None
    order: Optional[int] = None


class Lesson(LessonBase):
    id: int
    section_id: int

    class Config:
        from_attributes = True


class LessonWithProgress(Lesson):
    completed: bool = False
    last_accessed: Optional[str] = None
