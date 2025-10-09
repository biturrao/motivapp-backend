from pydantic import BaseModel, EmailStr
from typing import Optional # <-- Añade Optional si no está

# --- Schema base con los campos comunes
class UserBase(BaseModel):
    email: EmailStr

# --- Schema para la creación de un usuario (lo que la API recibe)
# AHORA INCLUYE LOS CAMPOS DEL PERFIL
class UserCreate(UserBase):
    password: str
    name: str
    age: Optional[int] = None
    institution: Optional[str] = None
    major: Optional[str] = None
    on_medication: Optional[str] = None
    has_learning_difficulties: Optional[str] = None

# --- Schema para leer un usuario (lo que la API devuelve)
class UserRead(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True