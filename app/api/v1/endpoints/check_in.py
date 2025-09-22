from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.crud import crud_daily_check_in
from app.schemas.daily_check_in import DailyCheckInCreate, DailyCheckInRead

router = APIRouter()

@router.post("/", response_model=DailyCheckInRead, status_code=status.HTTP_201_CREATED)
def submit_daily_check_in(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    check_in_in: DailyCheckInCreate
):
    """
    Guarda o actualiza el check-in de motivación diario para el usuario autenticado.
    """
    check_in = crud_daily_check_in.save_check_in(
        db=db, user_id=current_user.id, check_in_in=check_in_in
    )
    return check_in
