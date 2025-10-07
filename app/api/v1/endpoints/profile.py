# mot_back/app/api/v1/endpoints/profile.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.crud import crud_user_profile
from app.schemas.user_profile import UserProfileRead, UserProfileUpdate, UserProfileCreate

router = APIRouter()

@router.get("/profile/me", response_model=UserProfileRead)
def read_user_profile_me(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Obtener el perfil del usuario actual.
    """
    profile = crud_user_profile.get_profile(db, user_id=current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El perfil de usuario no ha sido creado todavía.",
        )
    return profile

@router.post("/profile/me", response_model=UserProfileRead)
def create_or_update_user_profile_me(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    profile_in: UserProfileUpdate,
):
    """
    Crear o actualizar el perfil del usuario actual.
    """
    profile = crud_user_profile.get_profile(db, user_id=current_user.id)
    
    if profile:
        # Si el perfil existe, lo actualizamos
        profile = crud_user_profile.update_profile(db=db, db_obj=profile, obj_in=profile_in)
    else:
        # Si no existe, lo creamos.
        # Verificamos que al menos el nombre venga en la primera creación.
        if not profile_in.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El campo 'name' es obligatorio al crear un perfil por primera vez.",
            )
        
        # Convertimos el schema de actualización a uno de creación
        profile_create = UserProfileCreate(**profile_in.model_dump())
        profile = crud_user_profile.create_profile(db=db, profile_in=profile_create, user_id=current_user.id)
        
    return profile