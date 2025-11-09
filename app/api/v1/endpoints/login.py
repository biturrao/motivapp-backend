from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional

from app.api import deps
from app.core import security
from app.core.config import settings
from app.crud import crud_user
from app.crud import crud_refresh_token
from app.schemas.token import Token, TokenWithRefresh, RefreshTokenRequest
from app.models.user import User

router = APIRouter()

@router.post("/login/access-token", response_model=TokenWithRefresh)
def login_for_access_token(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_agent: Optional[str] = Header(None)
):
    """
    OAuth2 compatible token login, get an access token and refresh token for future requests.
    """
    user = crud_user.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Crear access token con rol
    access_token = security.create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=access_token_expires
    )
    
    # Crear refresh token (válido por 30 días)
    refresh_token_obj = crud_refresh_token.create_user_refresh_token(
        db=db,
        user_id=user.id,
        device_info=user_agent or "unknown",
        expires_days=30
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_obj.token,
        "token_type": "bearer"
    }


@router.post("/login/refresh-token", response_model=Token)
def refresh_access_token(
    *,
    db: Session = Depends(deps.get_db),
    refresh_request: RefreshTokenRequest
):
    """
    Usa un refresh token válido para obtener un nuevo access token.
    """
    # Verificar que el refresh token existe y es válido
    refresh_token = crud_refresh_token.get_refresh_token(
        db=db,
        token=refresh_request.refresh_token
    )
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Obtener el usuario asociado
    user = crud_user.get_user_by_id(db=db, user_id=refresh_token.user_id)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo o no encontrado"
        )
    
    # Crear nuevo access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/logout")
def logout(
    *,
    db: Session = Depends(deps.get_db),
    refresh_request: RefreshTokenRequest
):
    """
    Revoca un refresh token específico (cierra sesión en un dispositivo).
    """
    revoked = crud_refresh_token.revoke_refresh_token(
        db=db,
        token=refresh_request.refresh_token
    )
    
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refresh token no encontrado"
        )
    
    return {"message": "Sesión cerrada exitosamente"}


@router.post("/login/logout-all")
def logout_all_devices(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Revoca todos los refresh tokens del usuario (cierra sesión en todos los dispositivos).
    """
    count = crud_refresh_token.revoke_all_user_tokens(
        db=db,
        user_id=current_user.id
    )
    
    return {"message": f"Sesión cerrada en {count} dispositivo(s)"}
