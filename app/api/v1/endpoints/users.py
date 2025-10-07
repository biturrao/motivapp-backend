from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.api import deps
from app.crud import crud_user
from app.schemas.user import UserCreate
from app.schemas.token import Token # <-- Importar Token
from app.core import security       # <-- Importar security
from app.core.config import settings # <-- Importar settings

router = APIRouter()

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED) # <-- Cambiar response_model a Token
def register_new_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate
):
    """
    Crea un nuevo usuario y devuelve un token de acceso.
    """
    user = crud_user.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado.",
        )
    
    user = crud_user.create_user(db, user=user_in)

    # --- LÓGICA AÑADIDA PARA INICIAR SESIÓN ---
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}