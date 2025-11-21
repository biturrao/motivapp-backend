# mot_back/app/crud/crud_user_profile.py

from sqlalchemy.orm import Session
from typing import Any, Dict, Union

from app.models.user_profile import UserProfile
from app.schemas.user_profile import UserProfileCreate, UserProfileUpdate

def get_profile(db: Session, user_id: int) -> UserProfile | None:
    """
    Obtiene el perfil de un usuario por su ID.
    """
    return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

def create_profile(db: Session, *, profile_in: UserProfileCreate, user_id: int) -> UserProfile:
    """
    Crea un nuevo perfil para un usuario.
    """
    profile_data = profile_in.model_dump(exclude_unset=True)
    db_profile = UserProfile(**profile_data, user_id=user_id)
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

def update_profile(
    db: Session,
    *,
    db_obj: UserProfile,
    obj_in: Union[UserProfileUpdate, Dict[str, Any]]
) -> UserProfile:
    """
    Actualiza un perfil existente.
    """
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj