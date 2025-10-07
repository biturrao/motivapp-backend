from pydantic import BaseModel
from typing import Optional

class UserProfileBase(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    institution: Optional[str] = None
    major: Optional[str] = None
    # --- CAMPOS MODIFICADOS ---
    on_medication: Optional[str] = None
    has_learning_difficulties: Optional[str] = None

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