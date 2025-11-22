from datetime import date
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.daily_check_in import DailyCheckIn
from app.crud import crud_daily_check_in
from app.schemas.daily_check_in import DailyCheckInCreate, DailyCheckInRead
from app.services import ai_service

router = APIRouter()

@router.post("/", response_model=DailyCheckInRead, status_code=status.HTTP_201_CREATED)
async def submit_daily_check_in(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    check_in_in: DailyCheckInCreate
):
    """
    Guarda o actualiza el check-in de motivación diario para el usuario autenticado.
    """
    # 1. Obtener el check-in anterior (antes de hoy) para comparar
    previous_check_in = db.query(DailyCheckIn).filter(
        DailyCheckIn.user_id == current_user.id,
        DailyCheckIn.date < date.today()
    ).order_by(DailyCheckIn.date.desc()).first()
    
    previous_level = previous_check_in.motivation_level if previous_check_in else None

    # 2. Guardar el nuevo check-in
    check_in = crud_daily_check_in.save_check_in(
        db=db, user_id=current_user.id, check_in_in=check_in_in
    )
    
    # 3. Generar feedback con IA
    feedback = await ai_service.generate_checkin_feedback(
        current_level=check_in.motivation_level,
        previous_level=previous_level
    )
    
    # 4. Adjuntar feedback a la respuesta
    response = DailyCheckInRead.model_validate(check_in)
    response.message = feedback["message"]
    response.action = feedback["action"]
    
    return response
