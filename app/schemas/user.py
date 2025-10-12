from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr

# --- Schema para la creación de un usuario (lo que la API recibe) ---
# ESTA ES LA CLASE CORREGIDA
class UserCreate(UserBase):
    password: str
    name: str
    age: Optional[int] = None
    institution: Optional[str] = None
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

# --- Schema para leer un usuario (lo que la API devuelve) ---
class UserRead(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True