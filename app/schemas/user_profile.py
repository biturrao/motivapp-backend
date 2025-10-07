# mot_back/app/schemas/user_profile.py

from pydantic import BaseModel
from typing import Optional

# --- Schema Base ---
# Contiene los campos comunes que se pueden crear o actualizar
class UserProfileBase(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    institution: Optional[str] = None
    major: Optional[str] = None
    on_medication: Optional[bool] = None
    has_learning_difficulties: Optional[bool] = None

# --- Schema para Crear ---
# Hereda de la base, pero hacemos el nombre obligatorio al crear
class UserProfileCreate(UserProfileBase):
    name: str

# --- Schema para Actualizar ---
# Es idéntico a la base, ya que todos los campos son opcionales al actualizar
class UserProfileUpdate(UserProfileBase):
    pass

# --- Schema para Leer ---
# Lo que la API devolverá, incluyendo el id del perfil y del usuario
class UserProfileRead(UserProfileBase):
    id: int
    user_id: int
    name: str # Hacemos que el nombre no sea opcional al leer

    class Config:
        from_attributes = True