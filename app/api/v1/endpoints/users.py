from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.api import deps
from app.crud import crud_user
from app.schemas.user import UserCreate, PsychologistCreate, UserRead
from app.schemas.token import Token
from app.core import security
from app.core.config import settings

router = APIRouter()

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_new_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate
):
    """
    Crea un nuevo usuario ALUMNO (student) y devuelve un token.
    """
    user = crud_user.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado.",
        )
    
    user = crud_user.create_user(db, user=user_in) # Esto crea un 'student'

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # --- CAMBIO: Añadir rol al token ---
    access_token = security.create_access_token(
        data={"sub": user.email, "role": user.role}, # <-- Añadido "role"
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


# --- CAMBIO: Nuevo endpoint para registrar psicólogos ---
@router.post("/register-psychologist", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_new_psychologist(
    *,
    db: Session = Depends(deps.get_db),
    user_in: PsychologistCreate
):
    """
    Crea un nuevo usuario PSICÓLOGO (admin) y devuelve un token.
    """
    user = crud_user.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado.",
        )
    
    user = crud_user.create_psychologist_user(db, user=user_in)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    access_token = security.create_access_token(
        data={"sub": user.email, "role": user.role}, # <-- "role" será "psychologist"
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
# --- Fin del cambio ---
