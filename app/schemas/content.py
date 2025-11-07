from pydantic import BaseModel
from typing import Optional
from enum import Enum


class ContentType(str, Enum):
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"


class ContentBase(BaseModel):
    title: str
    description: Optional[str] = None
    content_type: ContentType
    content_url: Optional[str] = None
    duration_minutes: Optional[int] = None
    order: int


class ContentCreate(ContentBase):
    section_id: int


class ContentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content_type: Optional[ContentType] = None
    content_url: Optional[str] = None
    duration_minutes: Optional[int] = None
    order: Optional[int] = None


class Content(ContentBase):
    id: int
    section_id: int

    class Config:
        from_attributes = True


class ContentWithProgress(Content):
    completed: bool = False
    last_accessed: Optional[str] = None
