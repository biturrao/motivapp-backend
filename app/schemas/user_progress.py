from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserContentProgressBase(BaseModel):
    content_id: int
    completed: bool = False


class UserContentProgressCreate(UserContentProgressBase):
    pass


class UserContentProgress(UserContentProgressBase):
    id: int
    user_id: int
    completed_at: Optional[datetime] = None
    last_accessed: datetime

    class Config:
        from_attributes = True


class UserLessonProgressBase(BaseModel):
    lesson_id: int
    completed: bool = False


class UserLessonProgressCreate(UserLessonProgressBase):
    pass


class UserLessonProgress(UserLessonProgressBase):
    id: int
    user_id: int
    completed_at: Optional[datetime] = None
    last_accessed: datetime

    class Config:
        from_attributes = True


class UserSectionProgressBase(BaseModel):
    section_id: int
    current_content_order: int = 1
    current_lesson_order: int = 1
    completed: bool = False


class UserSectionProgressCreate(UserSectionProgressBase):
    pass


class UserSectionProgress(UserSectionProgressBase):
    id: int
    user_id: int
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PathOverview(BaseModel):
    """Overview of user's entire path progress"""
    total_sections: int
    completed_sections: int
    current_section_id: Optional[int] = None
    current_section_name: Optional[str] = None
    overall_progress_percentage: float
