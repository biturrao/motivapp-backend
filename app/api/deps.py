from typing import Generator
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User
from app.crud import crud_user

# Esta es la URL donde el cliente puede obtener un token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login/access-token")

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependencia para obtener el usuario actual a partir de un token JWT.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        
        # --- CAMBIO: Validar que el token tenga la estructura esperada ---
        # Obtenemos el rol del token. Si no existe, es un token inválido/antiguo.
        role: str = payload.get("role")
        if email is None or role is None:
        # --- Fin del cambio ---
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = crud_user.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    
    # Nos aseguramos de que el rol en la DB coincida con el del token
    # (por si el rol del usuario cambió pero el token sigue siendo antiguo)
    if user.role != role:
        raise credentials_exception

    return user

# --- CAMBIO: Nueva dependencia para proteger rutas de psicólogos ---
def get_current_psychologist_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependencia que obtiene el usuario actual y verifica si es un psicólogo.
    Si no lo es, lanza un error 403 Forbidden.
    """
    if current_user.role != "psychologist":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes para acceder a este recurso."
        )
    return current_user
# --- Fin del cambio ---
