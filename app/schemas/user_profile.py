# mot_back/app/schemas/user_profile.py
from pydantic import BaseModel
from typing import Optional

class UserProfileBase(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    major: Optional[str] = None
    entry_year: Optional[int] = None
    course_types: Optional[str] = None
    family_responsibilities: Optional[str] = None
    is_working: Optional[str] = None
    mental_health_support: Optional[str] = None
    mental_health_details: Optional[str] = None
    chronic_condition: Optional[str] = None
    chronic_condition_details: Optional[str] = None
    neurodivergence: Optional[str] = None
    neurodivergence_details: Optional[str] = None
    preferred_support_types: Optional[str] = None

class UserProfileCreate(UserProfileBase):
    name: str

class UserProfileUpdate(UserProfileBase):
    pass

class UserProfileRead(UserProfileBase):
    id: int
    user_id: int
    name: str

    class Config:
        from_attributes = True