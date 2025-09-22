from pydantic import BaseModel, EmailStr

# --- Schemas para el manejo de Usuarios ---

# Schema base con los campos comunes
class UserBase(BaseModel):
    email: EmailStr

# Schema para la creación de un usuario (lo que la API recibe)
# Hereda de UserBase y añade la contraseña.
class UserCreate(UserBase):
    password: str

# Schema para leer un usuario (lo que la API devuelve)
# No incluye la contraseña por seguridad.
class UserRead(UserBase):
    id: int
    is_active: bool

    # Configuración para que Pydantic pueda leer datos desde un objeto SQLAlchemy
    class Config:
        from_attributes = True
