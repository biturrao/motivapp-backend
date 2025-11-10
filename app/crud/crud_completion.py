from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta

from app.models.exercise_completion import ExerciseCompletion
from app.schemas.wellness import ExerciseCompletionCreate, ExerciseCompletionUpdate


def create_completion(
    db: Session,
    user_id: int,
    completion_data: ExerciseCompletionCreate
) -> ExerciseCompletion:
    """Crear un nuevo registro de completación de ejercicio"""
    db_completion = ExerciseCompletion(
        user_id=user_id,
        **completion_data.model_dump()
    )
    db.add(db_completion)
    db.commit()
    db.refresh(db_completion)
    return db_completion


def get_completion(
    db: Session,
    completion_id: int
) -> Optional[ExerciseCompletion]:
    """Obtener una completación por ID"""
    return db.query(ExerciseCompletion).filter(
        ExerciseCompletion.id == completion_id
    ).first()


def get_user_completions(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[ExerciseCompletion]:
    """Obtener completaciones de un usuario"""
    return db.query(ExerciseCompletion).filter(
        ExerciseCompletion.user_id == user_id
    ).order_by(
        ExerciseCompletion.started_at.desc()
    ).offset(skip).limit(limit).all()


def get_todays_completions(
    db: Session,
    user_id: int
) -> List[ExerciseCompletion]:
    """Obtener completaciones de hoy para un usuario"""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    return db.query(ExerciseCompletion).filter(
        and_(
            ExerciseCompletion.user_id == user_id,
            ExerciseCompletion.started_at >= today_start
        )
    ).order_by(ExerciseCompletion.started_at.desc()).all()


def update_completion(
    db: Session,
    completion_id: int,
    completion_update: ExerciseCompletionUpdate
) -> Optional[ExerciseCompletion]:
    """Actualizar una completación (principalmente para marcar como completada)"""
    db_completion = get_completion(db, completion_id)
    
    if not db_completion:
        return None
    
    update_data = completion_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_completion, field, value)
    
    # Si se marca como completada, actualizar timestamp
    if completion_update.completed and db_completion.completed_at is None:
        db_completion.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_completion)
    return db_completion


def has_completed_exercise_today(
    db: Session,
    user_id: int,
    exercise_id: int
) -> bool:
    """Verificar si el usuario ya completó este ejercicio hoy"""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    completion = db.query(ExerciseCompletion).filter(
        and_(
            ExerciseCompletion.user_id == user_id,
            ExerciseCompletion.exercise_id == exercise_id,
            ExerciseCompletion.started_at >= today_start,
            ExerciseCompletion.completed == True
        )
    ).first()
    
    return completion is not None


def get_completion_streak(
    db: Session,
    user_id: int
) -> int:
    """
    Calcular racha de días consecutivos con al menos un ejercicio completado
    """
    completions = db.query(ExerciseCompletion).filter(
        and_(
            ExerciseCompletion.user_id == user_id,
            ExerciseCompletion.completed == True
        )
    ).order_by(ExerciseCompletion.started_at.desc()).all()
    
    if not completions:
        return 0
    
    # Obtener fechas únicas (solo día, sin hora)
    completion_dates = set()
    for c in completions:
        date_only = c.started_at.date()
        completion_dates.add(date_only)
    
    # Ordenar fechas de más reciente a más antigua
    sorted_dates = sorted(completion_dates, reverse=True)
    
    # Calcular racha
    streak = 0
    today = datetime.utcnow().date()
    
    for i, date in enumerate(sorted_dates):
        expected_date = today - timedelta(days=i)
        
        if date == expected_date:
            streak += 1
        else:
            break
    
    return streak


def get_exercise_completion_history(
    db: Session,
    user_id: int,
    exercise_id: int
) -> List[ExerciseCompletion]:
    """Obtener historial de completaciones de un ejercicio específico"""
    return db.query(ExerciseCompletion).filter(
        and_(
            ExerciseCompletion.user_id == user_id,
            ExerciseCompletion.exercise_id == exercise_id
        )
    ).order_by(ExerciseCompletion.started_at.desc()).all()


def get_total_completions(
    db: Session,
    user_id: int
) -> int:
    """Obtener el total de ejercicios completados por el usuario"""
    return db.query(ExerciseCompletion).filter(
        and_(
            ExerciseCompletion.user_id == user_id,
            ExerciseCompletion.completed == True
        )
    ).count()


def get_last_completion_date(
    db: Session,
    user_id: int
) -> Optional[str]:
    """Obtener la fecha de la última completación"""
    completion = db.query(ExerciseCompletion).filter(
        and_(
            ExerciseCompletion.user_id == user_id,
            ExerciseCompletion.completed == True
        )
    ).order_by(ExerciseCompletion.completed_at.desc()).first()
    
    if completion and completion.completed_at:
        return completion.completed_at.isoformat()
    return None

