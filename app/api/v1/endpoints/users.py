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
    (Esta función no tiene cambios de seguridad)
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


# --- CAMBIO: Endpoint de psicólogos actualizado con seguridad ---
@router.post("/register-psychologist", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_new_psychologist(
    *,
    db: Session = Depends(deps.get_db),
    user_in: PsychologistCreate # <-- El schema ahora contiene 'invite_key'
):
    """
    Crea un nuevo usuario PSICÓLOGO (admin) y devuelve un token.
    Ahora está protegido por una llave de invitación.
    """
    
    # --- INICIO DE LA LÓGICA DE SEGURIDAD ---
    # Comparamos la llave del frontend con la llave guardada en Render
    if user_in.invite_key != settings.PSYCHOLOGIST_INVITE_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Llave de invitación incorrecta.",
        )
    # --- FIN DE LA LÓGICA DE SEGURIDAD ---

    # Si la llave es correcta, procedemos a crear el usuario
    user = crud_user.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado.",
        )
    
    # Corregimos la llamada a la función CRUD
    user = crud_user.create_psychologist_user(
        db, 
        email=user_in.email, 
        password=user_in.password
    )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    access_token = security.create_access_token(
        data={"sub": user.email, "role": user.role}, # <-- "role" será "psychologist"
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}