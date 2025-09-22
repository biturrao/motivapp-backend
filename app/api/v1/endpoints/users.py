from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import crud_user
from app.schemas.user import UserCreate, UserRead

# Creamos un router para agrupar los endpoints de usuarios
router = APIRouter()

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_new_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate
):
    """
    Crea un nuevo usuario.
    """
    user = crud_user.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado.",
        )
    
    user = crud_user.create_user(db, user=user_in)
    return user
